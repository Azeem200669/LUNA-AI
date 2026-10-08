import atexit
import queue
import threading
import re
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from core.router import ModelRouter
from core.action_executor import ActionExecutor

from core.fast_router import FastRouter
from nlp.nlp_engine import NLPEngine
from nlp.planner import LunaPlanner
from core.memory import MemoryManager
from core.memory_retriever import MemoryRetriever
from core.memory_extractor import MemoryExtractor
from core.memory_controls import MemoryControls


# ============================================================
# DEDICATED BROWSER WORKER
# ============================================================
# Playwright's Python API is not thread-safe. One dedicated thread
# owns BrowserController for the entire lifetime of LunaAgent.
# UI/QThread callers communicate through a queue.
# This prevents temporary worker threads from destroying Playwright
# while the Node driver still has pending events, which was the source
# of the EPIPE seen after Phase 11.4.
# ============================================================


@dataclass
class _BrowserTask:
    method_name: str
    args: tuple
    kwargs: dict
    event: threading.Event
    result: Any = None
    error: Optional[BaseException] = None


class _BrowserWorker:
    def __init__(self):
        self._queue = queue.Queue()
        self._ready = threading.Event()
        self._controller = None
        self._stopping = False

        self._thread = threading.Thread(
            target=self._run,
            name="LUNA-Browser-Worker",
            daemon=True,
        )
        self._thread.start()
        self._ready.wait(timeout=2.0)

    def _run(self):
        self._ready.set()

        while True:
            task = self._queue.get()

            if task is None:
                break

            if task.method_name == "__shutdown__":
                try:
                    self._close_controller()
                finally:
                    task.event.set()
                break

            try:
                controller = self._ensure_controller()
                method = getattr(controller, task.method_name, None)

                if not callable(method):
                    raise AttributeError(
                        "BrowserController has no method "
                        f"'{task.method_name}'."
                    )

                task.result = method(
                    *task.args,
                    **task.kwargs,
                )

            except BaseException as error:
                task.error = error

            finally:
                task.event.set()

        self._controller = None

    def _ensure_controller(self):
        if self._controller is not None:
            return self._controller

        from browser.browser_controller import BrowserController

        controller = BrowserController()

        open_chrome = getattr(
            controller,
            "open_chrome",
            None,
        )

        if callable(open_chrome):
            open_chrome()

        self._controller = controller

        print(
            "[LUNA] BrowserController created on dedicated "
            f"browser thread {threading.get_ident()}."
        )

        return controller

    def call(self, method_name, *args, **kwargs):
        if threading.get_ident() == self._thread.ident:
            controller = self._ensure_controller()
            method = getattr(controller, method_name, None)

            if not callable(method):
                raise AttributeError(
                    "BrowserController has no method "
                    f"'{method_name}'."
                )

            return method(*args, **kwargs)

        if self._stopping:
            raise RuntimeError(
                "LUNA browser worker is stopping."
            )

        task = _BrowserTask(
            method_name=method_name,
            args=args,
            kwargs=kwargs,
            event=threading.Event(),
        )

        self._queue.put(task)
        task.event.wait()

        if task.error is not None:
            raise task.error

        return task.result

    def _close_controller(self):
        controller = self._controller

        if controller is None:
            return

        # Prefer an explicit lifecycle method if BrowserController exposes one.
        for name in (
            "close",
            "disconnect",
            "shutdown",
            "stop",
        ):
            method = getattr(controller, name, None)

            if callable(method):
                try:
                    method()
                except Exception as error:
                    print(
                        "[LUNA] Browser cleanup warning: "
                        f"{error}"
                    )
                return

        # Compatibility fallback for common internal attribute names.
        for attr_name in (
            "playwright",
            "_playwright",
        ):
            playwright = getattr(
                controller,
                attr_name,
                None,
            )

            stop = getattr(
                playwright,
                "stop",
                None,
            )

            if callable(stop):
                try:
                    stop()
                except Exception as error:
                    print(
                        "[LUNA] Playwright cleanup warning: "
                        f"{error}"
                    )
                return

    def shutdown(self):
        if self._stopping:
            return

        self._stopping = True

        task = _BrowserTask(
            method_name="__shutdown__",
            args=(),
            kwargs={},
            event=threading.Event(),
        )

        self._queue.put(task)
        task.event.wait(timeout=5.0)

        if self._thread.is_alive():
            self._thread.join(timeout=2.0)


class _BrowserProxy:
    """Proxy that sends every BrowserController method to one thread."""

    def __init__(self, worker):
        self._worker = worker

    def __getattr__(self, name):
        def method(*args, **kwargs):
            return self._worker.call(
                name,
                *args,
                **kwargs,
            )

        return method


class LunaAgent:
    """
    Main LUNA decision pipeline.

    Fast path:
        FastRouter
          -> file       -> FileRouter
          -> web        -> WebRouter / Tavily
          -> browser   -> direct BrowserController
          -> computer  -> local NLP + ActionExecutor
          -> ai        -> ModelRouter / Groq

    Multi-step requests are intentionally kept on the planner path because
    they require ordered action generation.
    """

    def __init__(self):
        # Existing AI / NLP components.
        self.router = ModelRouter()
        self.nlp = NLPEngine()
        self.planner = LunaPlanner()

        # New fast local classifier.
        self.fast_router = FastRouter()

        # Heavy routers are loaded only when their route is actually used.
        self._file_router = None
        self._web_router = None
        # Keep Playwright on one stable thread for the lifetime of the agent.
        self._browser_worker = _BrowserWorker()
        self._browser = _BrowserProxy(
            self._browser_worker
        )

        # Clean up the browser driver during normal interpreter shutdown.
        self._shutdown_complete = False

        # Persistent LUNA memory.
        self.memory = MemoryManager()
        self.memory_retriever = MemoryRetriever(self.memory)
        self.memory_extractor = MemoryExtractor()
        self.memory_controls = MemoryControls(self.memory)
        self.session_id = str(uuid.uuid4())

        try:
            atexit.register(self.shutdown)
        except Exception:
            pass

    def shutdown(self):
        """Cleanly stop LUNA's dedicated browser worker.

        The Playwright BrowserController is owned by the browser worker
        thread, so shutdown is delegated to that same worker thread.
        This keeps browser cleanup on the correct thread and prevents
        Playwright driver errors during interpreter shutdown.
        """
        if getattr(self, "_shutdown_complete", False):
            return

        worker = getattr(self, "_browser_worker", None)

        if worker is None:
            try:
                self.memory.close()
            except Exception:
                pass
            self._shutdown_complete = True
            return

        try:
            worker.shutdown()
        finally:
            try:
                self.memory.close()
            except Exception as error:
                print(f"[LUNA] Memory shutdown warning: {error}")
            self._shutdown_complete = True

    # ========================================================
    # CHAT
    # ========================================================

    def chat(self, message: str, model="auto"):
        """Main public chat entry point with persistent memory integration."""
        if not message or not message.strip():
            return "Please say something."

        message = message.strip()

        # Explicit memory/profile commands are handled before routing.
        memory_response = self.handle_memory_request(message)
        if memory_response is not None:
            self._record_turn(message, memory_response)
            return memory_response

        try:
            self.memory.add_message(
                self.session_id,
                "user",
                message,
            )
        except Exception as error:
            print(f"[LUNA] Memory write warning: {error}")

        try:
            response = self._chat_pipeline(message, model=model)
        except Exception as error:
            print(f"[LUNA] Chat error: {error}")
            raise

        try:
            self.memory.add_message(
                self.session_id,
                "assistant",
                str(response),
            )
        except Exception as error:
            print(f"[LUNA] Memory write warning: {error}")

        # Phase 12.3: automatically extract durable memories locally.
        try:
            extracted = self.memory_extractor.save(self.memory, message)
            if extracted:
                print(
                    "[LUNA MEMORY] Auto-saved: "
                    f"{extracted.get('memory_type')} -> "
                    f"{extracted.get('key') or extracted.get('value')}"
                )
        except Exception as error:
            print(f"[LUNA] Automatic memory warning: {error}")

        return response

    def _chat_pipeline(self, message: str, model="auto"):
        if not message or not message.strip():
            return "Please say something."

        message = message.strip()

        # ====================================================
        # MULTI-STEP FIRST
        # ====================================================
        #
        # Keep the existing working planner flow for requests
        # containing multiple ordered actions.
        #
        if self.looks_like_multi_step(message):
            print()
            print("[LUNA] Multi-step request detected.")

            plan = self.planner.create_plan(message)
            actions = plan.get("actions", []) if isinstance(plan, dict) else []

            if actions:
                print(f"[LUNA] Plan contains {len(actions)} actions.")

                results = ActionExecutor.execute(plan)
                return self.format_results(results)

            print("[LUNA] Planner returned no actions.")

        # ====================================================
        # FAST ROUTE
        # ====================================================

        route_result = self.fast_router.route(message)
        route = self._extract_route_name(route_result)

        print()
        print(f"[LUNA FAST ROUTER] Route: {route}")

        # ====================================================
        # FILE
        # ====================================================

        if route == "file":
            result = self.handle_file_request(message)

            if result is not None:
                return result

        # ====================================================
        # WEB / TAVILY
        # ====================================================

        if route == "web":
            result = self.handle_web_request(message)

            if result is not None:
                return result

        # ====================================================
        # BROWSER
        # ====================================================

        if route == "browser":
            result = self.handle_browser_request(message)

            if result is not None:
                return result

        # ====================================================
        # COMPUTER
        # ====================================================
        #
        # Local NLP handles known Windows commands without sending
        # them through the planner.
        #

        if route == "computer":
            result = self.handle_computer_request(message)

            if result is not None:
                return result

        # ====================================================
        # UNKNOWN / AI
        # ====================================================
        #
        # Only now run the normal NLP analysis. This preserves the
        # previous behavior for natural-language questions and any
        # command that the fast router did not confidently classify.
        #

        return self.handle_ai_request(message, model=model)


    # ========================================================
    # FAST ROUTE NORMALIZATION
    # ========================================================

    @staticmethod
    def _extract_route_name(route_result):
        """
        Accept the normal FastRouter string result, while also handling
        dictionary-style results so small router implementation changes do
        not break LunaAgent.
        """

        if isinstance(route_result, str):
            return route_result.strip().lower()

        if isinstance(route_result, dict):
            for key in (
                "route",
                "category",
                "type",
                "name",
                "intent",
            ):
                value = route_result.get(key)

                if isinstance(value, str) and value.strip():
                    return value.strip().lower()

        return "ai"

    # ========================================================
    # FILE ROUTER
    # ========================================================

    def _get_file_router(self):
        if self._file_router is None:
            self._file_router = self.fast_router.get_file_router()

        return self._file_router

    def handle_file_request(self, message):
        try:
            router = self._get_file_router()

            result = self._invoke_handler(
                router,
                message,
                preferred_methods=(
                    "handle",
                    "process",
                    "execute",
                    "ask",
                ),
            )

            normalized = self._normalize_handler_result(result)

            if normalized is not None:
                print("[LUNA] File request handled by FileRouter.")
                return normalized

        except Exception as error:
            print(f"[LUNA] File route error: {error}")

        return None

    # ========================================================
    # WEB ROUTER / TAVILY
    # ========================================================

    def _get_web_router(self):
        if self._web_router is None:
            self._web_router = self.fast_router.get_web_router()

        return self._web_router

    def handle_web_request(self, message):
        try:
            router = self._get_web_router()

            result = self._invoke_handler(
                router,
                message,
                preferred_methods=(
                    "handle",
                    "process",
                    "ask",
                    "search",
                ),
            )

            normalized = self._normalize_handler_result(result)

            if normalized is not None:
                print("[LUNA] Web request handled by WebRouter.")
                return normalized

        except Exception as error:
            print(f"[LUNA] Web route error: {error}")

        return None

    # ========================================================
    # BROWSER FAST PATH
    # ========================================================

    def _get_browser(self):
        return self._browser

    def handle_browser_request(self, message):
        """
        Handle common browser commands locally.

        Examples:
            "go to YouTube"
            "open YouTube"
            "search YouTube for AI tutorials"
            "search Google for Python tutorials"
            "go back"
            "go forward"
            "refresh"
            "new tab"
            "close tab"
            "what is the page title"
            "what is the current URL"

        Unknown browser commands fall back to the existing planner so the
        browser capabilities you already implemented remain available.
        """

        browser = self._get_browser()

        if browser is None:
            return None

        text = self._clean_text(message)

        try:
            # ------------------------------------------------
            # Navigation
            # ------------------------------------------------

            if self._contains_any(
                text,
                (
                    "go back",
                    "back",
                    "previous page",
                ),
            ):
                return self._call_browser(
                    browser,
                    ("back",),
                    "Went back."
                )

            if self._contains_any(
                text,
                (
                    "go forward",
                    "forward",
                    "next page",
                ),
            ):
                return self._call_browser(
                    browser,
                    ("forward",),
                    "Went forward."
                )

            if self._contains_any(
                text,
                (
                    "refresh",
                    "reload page",
                    "reload",
                ),
            ):
                return self._call_browser(
                    browser,
                    ("refresh",),
                    "Page refreshed."
                )

            if self._contains_any(
                text,
                (
                    "new tab",
                    "open new tab",
                ),
            ):
                return self._call_browser(
                    browser,
                    ("new_tab",),
                    "Opened a new tab."
                )

            if self._contains_any(
                text,
                (
                    "close tab",
                    "close this tab",
                ),
            ):
                return self._call_browser(
                    browser,
                    ("close_tab",),
                    "Closed the tab."
                )

            # ------------------------------------------------
            # Page information
            # ------------------------------------------------

            if self._contains_any(
                text,
                (
                    "page title",
                    "title of the page",
                    "what is the title",
                    "get title",
                ),
            ):
                value = self._call_browser_value(
                    browser,
                    ("get_title", "title"),
                )

                if value is not None:
                    return f"The page title is {value}."

            if self._contains_any(
                text,
                (
                    "current url",
                    "page url",
                    "website url",
                    "what is the url",
                    "get url",
                ),
            ):
                value = self._call_browser_value(
                    browser,
                    ("get_url", "url"),
                )

                if value is not None:
                    return f"The current URL is {value}."

            # ------------------------------------------------
            # Search engines
            # ------------------------------------------------

            youtube_query = self._extract_after_phrases(
                text,
                (
                    "search youtube for ",
                    "search youtube ",
                    "youtube search for ",
                    "youtube search ",
                ),
            )

            if youtube_query:
                return self._call_browser_search(
                    browser,
                    youtube_query,
                    (
                        "youtube_search",
                        "search_youtube",
                        "youtube_search_interactive",
                    ),
                    "Searched YouTube for",
                )

            google_query = self._extract_after_phrases(
                text,
                (
                    "search google for ",
                    "search google ",
                    "google search for ",
                    "google search ",
                    "search for ",
                ),
            )

            if google_query:
                return self._call_browser_search(
                    browser,
                    google_query,
                    (
                        "google_search",
                        "search_google",
                        "google_search_interactive",
                    ),
                    "Searched Google for",
                )

            # ------------------------------------------------
            # First search result
            # ------------------------------------------------

            if self._contains_any(
                text,
                (
                    "first result",
                    "first search result",
                    "open the first result",
                    "click the first result",
                ),
            ):
                value = self._call_browser_value(
                    browser,
                    (
                        "click_first_result",
                        "click_first_search_result",
                        "first_result",
                    ),
                )

                if value is not None:
                    return self._normalize_handler_result(value)

            # ------------------------------------------------
            # Direct website navigation
            # ------------------------------------------------

            website = self._extract_direct_website(text)

            if website:
                self._call_browser_value(
                    browser,
                    ("open_url",),
                    website,
                )
                return f"Opened {website}."

        except Exception as error:
            print(f"[LUNA] Browser fast-path error: {error}")

        # Unknown browser command:
        # preserve the existing complete planner/browser capability.
        return self._run_planner_fallback(message)

    # ========================================================
    # COMPUTER FAST PATH
    # ========================================================

    def handle_computer_request(self, message):
        try:
            analysis = self._analyze_single_command(message)

            print()
            print("🌐 LUNA NLP")
            print(f"Language: {analysis.get('language_name')}")
            print(f"Intent: {analysis.get('intent')}")
            print(f"Entity: {analysis.get('entity')}")
            print(f"Confidence: {analysis.get('confidence', 0.0):.2f}")
            print(f"Source: {analysis.get('source')}")

            if analysis.get("is_command"):
                result = self.execute_single_command(analysis)

                if result is not None:
                    return result

        except Exception as error:
            print(f"[LUNA] Computer route error: {error}")

        return None

    # ========================================================
    # MEMORY
    # ========================================================

    def _record_turn(self, user_message: str, assistant_message: str) -> None:
        try:
            self.memory.add_message(
                self.session_id,
                "user",
                user_message,
            )
            self.memory.add_message(
                self.session_id,
                "assistant",
                assistant_message,
            )
        except Exception as error:
            print(f"[LUNA] Memory write warning: {error}")

    @staticmethod
    def _strip_luna_prefix(text: str) -> str:
        text = text.strip()
        text = re.sub(r"^luna\s*[,;:]?\s*", "", text, flags=re.IGNORECASE)
        return text.strip()

    @staticmethod
    def _clean_memory_value(value: str) -> str:
        value = re.sub(r"\s+", " ", value.strip())
        return value.strip(" \t\r\n.,!?;:")

    @staticmethod
    def _memory_key_from_text(content: str) -> tuple[str | None, str]:
        text = content.strip()

        # Name / identity.
        name_match = re.match(
            r"(?:my\s+name\s+is|call\s+me)\s+(.+)$",
            text,
            flags=re.IGNORECASE,
        )
        if name_match:
            return "name", "profile"

        # Common preference wording.
        favorite_match = re.match(
            r"my\s+favorite\s+(.+?)\s+is\s+.+$",
            text,
            flags=re.IGNORECASE,
        )
        if favorite_match:
            subject = favorite_match.group(1).strip()
            key = "favorite_" + re.sub(r"[^a-z0-9]+", "_", subject.lower()).strip("_")
            return key or None, "preference"

        preferred_match = re.match(
            r"my\s+preferred\s+(.+?)\s+is\s+.+$",
            text,
            flags=re.IGNORECASE,
        )
        if preferred_match:
            subject = preferred_match.group(1).strip()
            key = "preferred_" + re.sub(r"[^a-z0-9]+", "_", subject.lower()).strip("_")
            return key or None, "preference"

        if re.search(r"\bmy\s+project\b", text, re.IGNORECASE):
            return "project", "project"

        return None, "fact"

    def handle_memory_request(self, message: str):
        """Handle explicit remember/name/memory queries before normal routing."""
        text = self._strip_luna_prefix(message)
        lower = text.lower()

        # Phase 12.5: explicit memory edit/delete commands.
        try:
            control_response = self.memory_controls.handle(text)
            if control_response is not None:
                return control_response
        except Exception as error:
            print(f"[LUNA] Memory control warning: {error}")

        # ----------------------------------------------------
        # Store the user's name even without the word 'remember'.
        # ----------------------------------------------------
        name_match = re.match(
            r"(?:my\s+name\s+is|call\s+me)\s+(.+)$",
            text,
            flags=re.IGNORECASE,
        )
        if name_match:
            name = self._clean_memory_value(name_match.group(1))
            if name:
                self.memory.set_name(name)
                return f"Nice to meet you, {name}. I'll remember your name."

        remember_match = re.match(
            r"(?:please\s+)?(?:remember|don't\s+forget|do\s+not\s+forget)(?:\s+that)?\s+(.+)$",
            text,
            flags=re.IGNORECASE,
        )
        if remember_match:
            content = self._clean_memory_value(remember_match.group(1))
            if content:
                key, memory_type = self._memory_key_from_text(content)

                # Special case: 'remember my name is X'.
                name_match = re.match(
                    r"my\s+name\s+is\s+(.+)$",
                    content,
                    flags=re.IGNORECASE,
                )
                if name_match:
                    name = self._clean_memory_value(name_match.group(1))
                    self.memory.set_name(name)
                    return f"I'll remember your name is {name}."

                self.memory.remember(
                    value=content,
                    memory_type=memory_type,
                    key=key,
                    source="explicit_user",
                    confidence=1.0,
                )

                if memory_type == "preference":
                    return "I'll remember that preference."
                if memory_type == "project":
                    return "I'll remember that project information."
                return "I'll remember that."

        # ----------------------------------------------------
        # Name queries.
        # ----------------------------------------------------
        name_query = {
            "what is my name",
            "what's my name",
            "do you know my name",
            "do you remember my name",
            "who am i",
        }
        if lower.rstrip("?.!") in name_query:
            name = self.memory.get_name()
            if name:
                return f"Your name is {name}."
            return "I don't know your name yet. You can tell me, for example, 'My name is Shaik.'"

        # ----------------------------------------------------
        # General memory query.
        # ----------------------------------------------------
        memory_queries = (
            "what do you remember about me",
            "what do you remember",
            "show my memories",
            "show what you remember",
            "list my memories",
        )
        if any(lower.rstrip("?.!") == item for item in memory_queries):
            memories = self.memory.list_memories(limit=20)
            if not memories:
                return "I don't have any saved memories yet."

            lines = ["Here is what I remember:"]
            for item in memories:
                key = item.get("memory_key")
                value = item.get("memory_value", "")
                memory_type = item.get("memory_type", "fact")

                if key:
                    lines.append(f"- {key}: {value} ({memory_type})")
                else:
                    lines.append(f"- {value} ({memory_type})")

            return "\n".join(lines)

        # ----------------------------------------------------
        # Clear conversation session without removing memories.
        # ----------------------------------------------------
        clear_queries = (
            "clear this conversation",
            "clear conversation",
            "forget this conversation",
        )
        if lower.rstrip("?.!") in clear_queries:
            deleted = self.memory.clear_session(self.session_id)
            return f"Cleared {deleted} conversation messages. Your saved memories are still kept."

        return None

    def build_memory_context(self, current_message: str, memory_limit: int = 6, history_limit: int = 8) -> str:
        """Build AI context using only memories relevant to the current request."""
        try:
            memories = self.memory_retriever.retrieve(
                current_message,
                limit=memory_limit,
            )
        except Exception as error:
            print(f"[LUNA] Memory retrieval warning: {error}")
            memories = []

        # Prefer the current session here. Persistent long-term memories are
        # already stored separately, so unrelated conversations from another
        # session should not be injected into the current prompt.
        try:
            history = self.memory.get_recent_messages(
                self.session_id,
                limit=history_limit,
            )
        except Exception as error:
            print(f"[LUNA] Conversation memory warning: {error}")
            history = []

        sections = []

        if memories:
            memory_lines = []
            for item in memories:
                key = item.get("memory_key")
                value = item.get("memory_value", "")
                memory_type = item.get("memory_type", "fact")
                if key:
                    line = f"{key}: {value} [{memory_type}]"
                else:
                    line = f"{value} [{memory_type}]"

                memory_lines.append(line)

            sections.append(
                "Relevant saved long-term memory (user-provided; use only when relevant):\n"
                + "\n".join(memory_lines)
            )

        if history:
            history_lines = []
            for item in history:
                role = item.get("role", "user")
                content = item.get("content", "")
                history_lines.append(f"{role}: {content}")

            sections.append(
                "Recent conversation context:\n"
                + "\n".join(history_lines)
            )

        if not sections:
            return current_message

        return (
            "You are LUNA, a personal AI assistant.\n"
            "Use the following private memory and recent conversation only as context. "
            "Do not mention or expose this context unless it is relevant to the user's request. "
            "When memory is relevant, answer naturally as if you remember the user. "
            "Do not invent memories or claim to remember anything not present below.\n\n"
            + "\n\n".join(sections)
            + "\n\nCurrent user request:\n"
            + current_message
        )

    # ========================================================
    # AI
    # ========================================================

    def handle_ai_request(self, message, model="auto"):
        analysis = self._analyze_single_command(message)

        print()
        print("🌐 LUNA NLP")
        print(f"Language: {analysis.get('language_name')}")
        print(f"Intent: {analysis.get('intent')}")
        print(f"Entity: {analysis.get('entity')}")
        print(f"Confidence: {analysis.get('confidence', 0.0):.2f}")
        print(f"Source: {analysis.get('source')}")

        if analysis.get("is_command"):
            result = self.execute_single_command(analysis)

            if result is not None:
                return result

        prompt = self.build_memory_context(message)

        return self.router.ask(
            prompt,
            model=model,
        )

    def _analyze_single_command(self, message):
        return self.nlp.analyze(message)

    # ========================================================
    # MULTI-STEP DETECTION
    # ========================================================

    def looks_like_multi_step(self, message):
        text = (
            message
            .lower()
            .strip()
        )

        # English
        connectors = (
            " and ",
            " then ",
            " after that ",
            " next ",
            " also ",
            " followed by ",
        )

        for connector in connectors:
            if connector in text:
                return True

        # Romanized / mixed language
        mixed_connectors = (
            " ani ",
            " mariyu ",
            " tarvata ",
            " taruvatha ",
            " phir ",
            " aur ",
            " fir ",
            " appuram ",
            " apram ",
        )

        for connector in mixed_connectors:
            if connector in text:
                return True

        return False

    # ========================================================
    # SINGLE COMMAND
    # ========================================================

    def execute_single_command(self, analysis):
        return ActionExecutor.execute_action(
            {
                "action": analysis.get("intent"),
                "target": analysis.get("entity"),
                "text": analysis.get("text"),
                "key": analysis.get("key"),
                "x": analysis.get("x"),
                "y": analysis.get("y"),
            }
        )

    # ========================================================
    # PLANNER FALLBACK
    # ========================================================

    def _run_planner_fallback(self, message):
        try:
            plan = self.planner.create_plan(message)

            actions = (
                plan.get("actions", [])
                if isinstance(plan, dict)
                else []
            )

            if actions:
                print(
                    f"[LUNA] Planner fallback contains "
                    f"{len(actions)} actions."
                )

                results = ActionExecutor.execute(plan)
                return self.format_results(results)

        except Exception as error:
            print(f"[LUNA] Planner fallback error: {error}")

        return None

    # ========================================================
    # GENERIC ROUTER INVOCATION
    # ========================================================

    @staticmethod
    def _invoke_handler(
        handler,
        message,
        preferred_methods=(),
    ):
        if handler is None:
            return None

        for method_name in preferred_methods:
            method = getattr(handler, method_name, None)

            if callable(method):
                return method(message)

        # Final compatibility fallback.
        if callable(handler):
            return handler(message)

        return None

    # ========================================================
    # RESULT NORMALIZATION
    # ========================================================

    @classmethod
    def _normalize_handler_result(cls, result):
        if result is None:
            return None

        if isinstance(result, str):
            value = result.strip()
            return value if value else None

        if isinstance(result, bytes):
            value = result.decode(
                "utf-8",
                errors="replace",
            ).strip()
            return value if value else None

        if isinstance(result, (list, tuple)):
            parts = []

            for item in result:
                normalized = cls._normalize_handler_result(item)

                if normalized:
                    parts.append(normalized)

            if parts:
                return " ".join(parts)

            return None

        if isinstance(result, dict):
            # Respect an explicit failure/handled flag.
            if result.get("handled") is False:
                return None

            for key in (
                "response",
                "answer",
                "message",
                "reply",
                "text",
                "result",
                "output",
            ):
                value = result.get(key)

                if isinstance(value, str) and value.strip():
                    return value.strip()

            # Some routers return result dictionaries containing lists.
            nested = result.get("results")

            if isinstance(nested, list):
                normalized = cls._normalize_handler_result(nested)

                if normalized:
                    return normalized

            return None

        return str(result)

    # ========================================================
    # BROWSER HELPERS
    # ========================================================

    @staticmethod
    def _clean_text(message):
        text = message.strip().lower()

        prefixes = (
            "luna,",
            "luna ",
            "hey luna,",
            "hey luna ",
        )

        changed = True

        while changed:
            changed = False

            for prefix in prefixes:
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()
                    changed = True

        return text

    @staticmethod
    def _contains_any(text, phrases):
        return any(
            phrase in text
            for phrase in phrases
        )

    @staticmethod
    def _extract_after_phrases(text, phrases):
        for phrase in phrases:
            if phrase in text:
                value = text.split(
                    phrase,
                    1,
                )[1].strip(" .,!?")

                if value:
                    return value

        return None

    @staticmethod
    def _extract_direct_website(text):
        sites = (
            ("youtube", "https://www.youtube.com"),
            ("google", "https://www.google.com"),
            ("github", "https://github.com"),
            ("gmail", "https://mail.google.com"),
            ("chatgpt", "https://chatgpt.com"),
            ("instagram", "https://www.instagram.com"),
        )

        if text in {
            "youtube",
            "open youtube",
            "go to youtube",
            "open youtube.com",
            "go to youtube.com",
        }:
            return "https://www.youtube.com"

        if text in {
            "google",
            "open google",
            "go to google",
            "open google.com",
            "go to google.com",
        }:
            return "https://www.google.com"

        for name, url in sites:
            if (
                text == name
                or text == f"open {name}"
                or text == f"go to {name}"
                or text == f"open {name}.com"
                or text == f"go to {name}.com"
            ):
                return url

        return None

    @staticmethod
    def _call_browser(
        browser,
        method_names,
        fallback_message,
    ):
        for method_name in method_names:
            method = getattr(browser, method_name, None)

            if callable(method):
                result = method()

                normalized = LunaAgent._normalize_handler_result(
                    result
                )

                if normalized:
                    return normalized

                return fallback_message

        return fallback_message

    @staticmethod
    def _call_browser_value(
        browser,
        method_names,
        *args,
    ):
        for method_name in method_names:
            method = getattr(browser, method_name, None)

            if callable(method):
                return method(*args)

        return None

    @staticmethod
    def _call_browser_search(
        browser,
        query,
        method_names,
        label,
    ):
        for method_name in method_names:
            method = getattr(browser, method_name, None)

            if callable(method):
                result = method(query)

                normalized = LunaAgent._normalize_handler_result(
                    result
                )

                if normalized:
                    return normalized

                return f"{label} {query}."

        return None

    # ========================================================
    # FORMAT RESULTS
    # ========================================================

    def format_results(self, results):
        messages = []

        if results is None:
            return "I couldn't complete the requested actions."

        # Existing ActionExecutor format.
        if isinstance(results, dict):
            results = [results]

        for item in results:
            if isinstance(item, str):
                if item.strip():
                    messages.append(item.strip())
                continue

            if not isinstance(item, dict):
                normalized = self._normalize_handler_result(item)

                if normalized:
                    messages.append(normalized)

                continue

            result = item.get("result")

            if result:
                normalized = self._normalize_handler_result(result)

                if normalized:
                    messages.append(normalized)

        if not messages:
            return "I couldn't complete the requested actions."

        if len(messages) == 1:
            return messages[0]

        return " ".join(messages)


if __name__ == "__main__":
    # Simple manual smoke test.
    agent = LunaAgent()

    tests = (
        "Luna, find agent.py",
        "Luna, open YouTube",
        "Luna, search YouTube for AI tutorials",
        "Luna, open Notepad",
        "What is machine learning?",
    )

    for command in tests:
        print()
        print("=" * 70)
        print("USER:", command)
        print("=" * 70)

        try:
            answer = agent.chat(command, model="groq")
            print("LUNA:", answer)
        except Exception as error:
            print("ERROR:", error)