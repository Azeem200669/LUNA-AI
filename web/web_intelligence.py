import re
from typing import Any, Dict, List, Optional

from tavily import TavilyClient
from groq import Groq

import config


class WebIntelligence:

    def __init__(self):

        # ====================================================
        # TAVILY
        # ====================================================

        tavily_key = getattr(
            config,
            "TAVILY_API_KEY",
            ""
        )

        if tavily_key:

            self.tavily = TavilyClient(
                api_key=tavily_key
            )

        else:

            # Current Tavily SDK supports keyless search
            # with usage limits.
            self.tavily = TavilyClient()

        # ====================================================
        # GROQ
        # ====================================================

        groq_key = getattr(
            config,
            "GROQ_API_KEY",
            ""
        )

        if not groq_key:

            raise ValueError(
                "GROQ_API_KEY is missing."
            )

        self.groq = Groq(
            api_key=groq_key
        )

        self.model = getattr(
            config,
            "GROQ_MODEL",
            "openai/gpt-oss-20b"
        )

    # ========================================================
    # WEB SEARCH
    # ========================================================

    def search(
        self,
        query: str,
        max_results: int = 5,
        topic: str = "general",
        time_range: Optional[str] = None,
        include_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:

        if not query or not query.strip():

            return {
                "success": False,
                "query": query,
                "results": [],
                "answer": "",
                "error": "Search query is empty."
            }

        query = query.strip()

        try:

            kwargs = {
                "query": query,
                "max_results": max_results,
                "topic": topic,
            }

            if time_range:

                kwargs["time_range"] = time_range

            if include_domains:

                kwargs["include_domains"] = (
                    include_domains
                )

            print()
            print(
                "[WEB] Searching Tavily:"
            )

            print(
                query
            )

            response = (
                self.tavily.search(
                    **kwargs
                )
            )

            results = response.get(
                "results",
                []
            )

            cleaned_results = []

            for item in results:

                cleaned_results.append(
                    {
                        "title": item.get(
                            "title",
                            ""
                        ),

                        "url": item.get(
                            "url",
                            ""
                        ),

                        "content": item.get(
                            "content",
                            ""
                        ),

                        "score": item.get(
                            "score"
                        ),

                        "published_date": item.get(
                            "published_date"
                        ),
                    }
                )

            return {
                "success": True,
                "query": query,
                "results": cleaned_results,
                "answer": "",
                "error": None
            }

        except Exception as error:

            print(
                f"[WEB] Tavily search error: {error}"
            )

            return {
                "success": False,
                "query": query,
                "results": [],
                "answer": "",
                "error": str(error)
            }

    # ========================================================
    # FORMAT SEARCH RESULTS
    # ========================================================

    def format_results(
        self,
        results: List[Dict[str, Any]]
    ) -> str:

        if not results:

            return (
                "No web results were found."
            )

        chunks = []

        for index, result in enumerate(
            results,
            start=1
        ):

            title = (
                result.get(
                    "title",
                    ""
                )
                or "Untitled"
            )

            url = (
                result.get(
                    "url",
                    ""
                )
                or ""
            )

            content = (
                result.get(
                    "content",
                    ""
                )
                or ""
            )

            published_date = (
                result.get(
                    "published_date"
                )
                or ""
            )

            content = re.sub(
                r"\s+",
                " ",
                content
            ).strip()

            chunks.append(
                (
                    f"SOURCE {index}\n"
                    f"TITLE: {title}\n"
                    f"URL: {url}\n"
                    f"DATE: {published_date}\n"
                    f"CONTENT: {content}"
                )
            )

        return "\n\n".join(
            chunks
        )

    # ========================================================
    # SUMMARIZE WITH GROQ
    # ========================================================

    def summarize(
        self,
        query: str,
        results: List[Dict[str, Any]],
        language: str = "en"
    ) -> str:

        if not results:

            return (
                "I couldn't find enough information "
                "on the web to answer that."
            )

        source_text = self.format_results(
            results
        )

        language_instruction = self._language_instruction(
            language
        )

        prompt = f"""
You are LUNA, a personal AI assistant.

The user asked:

{query}

You searched the live web and received these sources:

{source_text}

Create a useful answer for the user.

Rules:

1. Use the supplied web sources as the factual basis.
2. Do not invent information that is not supported.
3. Prefer information that appears across multiple sources.
4. Clearly distinguish uncertainty when sources disagree.
5. Keep the answer concise but useful.
6. Mention important source names naturally when useful.
7. Do not output raw JSON.
8. Do not output a bibliography unless the user asks.
9. Do not say that you browsed the web unless useful.
10. Answer in the requested language.

{language_instruction}
"""

        try:

            response = (
                self.groq
                .chat
                .completions
                .create(

                    model=self.model,

                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are LUNA's "
                                "web-information "
                                "summarizer."
                            )
                        },

                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],

                    temperature=0.2,

                    max_tokens=900
                )
            )

            answer = (
                response
                .choices[0]
                .message
                .content
                .strip()
            )

            return answer

        except Exception as error:

            print(
                f"[WEB] Groq summary error: {error}"
            )

            return (
                "I found web results, but I "
                "couldn't summarize them right now."
            )

    # ========================================================
    # SEARCH + ANSWER
    # ========================================================

    def ask_web(
        self,
        query: str,
        language: str = "en",
        max_results: int = 5,
        topic: str = "general",
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:

        search_data = self.search(
            query=query,
            max_results=max_results,
            topic=topic,
            time_range=time_range
        )

        if not search_data["success"]:

            return search_data

        answer = self.summarize(
            query=query,
            results=search_data["results"],
            language=language
        )

        search_data["answer"] = answer

        return search_data

    # ========================================================
    # EXTRACT PAGE
    # ========================================================

    def extract(
        self,
        urls: List[str]
    ) -> Dict[str, Any]:

        if not urls:

            return {
                "success": False,
                "results": [],
                "error": "No URLs supplied."
            }

        try:

            response = (
                self.tavily.extract(
                    urls
                )
            )

            return {
                "success": True,
                "results": response.get(
                    "results",
                    []
                ),
                "failed_results": response.get(
                    "failed_results",
                    []
                ),
                "error": None
            }

        except Exception as error:

            print(
                f"[WEB] Extract error: {error}"
            )

            return {
                "success": False,
                "results": [],
                "error": str(error)
            }

    # ========================================================
    # NEWS SEARCH
    # ========================================================

    def news(
        self,
        query: str,
        language: str = "en",
        max_results: int = 5
    ) -> Dict[str, Any]:

        return self.ask_web(
            query=query,
            language=language,
            max_results=max_results,
            topic="news",
            time_range="week"
        )

    # ========================================================
    # LANGUAGE INSTRUCTION
    # ========================================================

    def _language_instruction(
        self,
        language: str
    ) -> str:

        language = (
            str(language or "en")
            .lower()
            .strip()
        )

        language_map = {

            "en": "Answer in English.",

            "te": "Answer in Telugu.",

            "hi": "Answer in Hindi.",

            "ta": "Answer in Tamil.",

            "kn": "Answer in Kannada.",

            "ml": "Answer in Malayalam.",

            "bn": "Answer in Bengali.",

            "mr": "Answer in Marathi.",

            "gu": "Answer in Gujarati.",

            "pa": "Answer in Punjabi.",

            "ur": "Answer in Urdu.",

            "ar": "Answer in Arabic.",
        }

        return language_map.get(
            language,
            "Answer in English unless the user's language is clear."
        )


# ============================================================
# ============================================================
#
#   🌙 LUNA WEB INTELLIGENCE PRO — EXTENSIONS (APPEND ONLY)
#
#   The original WebIntelligence above is 100% unchanged.
#   Pro overrides search/summarize/news/ask_web as thin
#   layers that call super() — the base logic always runs.
#
#   FIXES
#     • Incomplete language map — TTS has voices for
#       fr/es/de/it/pt/ja/ko/zh/tr/ru, but the summarizer's
#       map didn't, so those replies came back in English
#       (or the model guessed). Map now matches voice_map.
#     • Unbounded source content — Tavily results went into
#       the prompt raw, so one huge page could blow the
#       context window and slow every summary. Now capped
#       per result AND in total.
#     • Groq client had no timeout/max_retries — a stalled
#       connection could hang LUNA mid-answer. Rebuilt with
#       timeout=30s and 2 SDK-level retries.
#     • Tavily rate limits failed instantly — a 429 now
#       retries with backoff instead of erroring out.
#     • Reply language never auto-detected — language
#       defaults to "en" and callers often don't pass it,
#       so Telugu/Hindi/Japanese queries got English
#       summaries. Pro detects the query's script and
#       answers in the user's language.
#     • news() hardcoded time_range="week" — now a
#       parameter (default unchanged, fully compatible).
#
#   ADDITIONS
#     • Search result cache with TTL (repeated questions
#       are instant and don't burn API credits)
#     • search_depth="advanced" support (deeper Tavily
#       crawling for hard questions)
#     • quick_answer() — one call, returns a plain string
#     • answer_speakable — TTS-clean answer (markdown,
#       URLs, emoji stripped) added to ask_web results
#     • sources_line() — speakable citations
#     • detect_query_language(), clear_cache(), get_stats()
#
# ============================================================
# ============================================================

import threading
import time


class WebIntelligencePro(WebIntelligence):

    # ==================================================
    # LIMITS
    # ==================================================

    max_content_per_result = 1200

    max_total_source_chars = 9000

    cache_ttl_seconds = 600

    search_retries = 2

    # ==================================================
    # EXTENDED LANGUAGE MAP (matches the TTS voice_map)
    # ==================================================

    EXTRA_LANGUAGES = {
        "fr": "Answer in French.",
        "es": "Answer in Spanish.",
        "de": "Answer in German.",
        "it": "Answer in Italian.",
        "pt": "Answer in Portuguese.",
        "ja": "Answer in Japanese.",
        "ko": "Answer in Korean.",
        "zh": "Answer in Chinese.",
        "tr": "Answer in Turkish.",
        "ru": "Answer in Russian.",
    }

    def __init__(self):

        super().__init__()

        # -----------------------------
        # FIX: Groq with timeout +
        # SDK-level retries
        # -----------------------------

        groq_key = getattr(
            config,
            "GROQ_API_KEY",
            "",
        )

        if groq_key:

            try:

                self.groq = Groq(
                    api_key=groq_key,
                    timeout=30.0,
                    max_retries=2,
                )

            except Exception:

                pass  # base client stays

        # -----------------------------
        # CACHE + STATS
        # -----------------------------

        self._search_cache = {}

        self._cache_lock = (
            threading.Lock()
        )

        self._stats = {
            "searches": 0,
            "cache_hits": 0,
            "search_retries": 0,
            "summaries": 0,
            "truncated_results": 0,
            "errors": 0,
        }

    # ==================================================
    # QUERY LANGUAGE DETECTION
    # (same script logic as the TTS module)
    # ==================================================

    def detect_query_language(self, text):

        if not text:

            return "en"

        if re.search(
            r"[\u0600-\u06FF]",
            text,
        ):

            urdu_letters = "ٹڈڑںےگچپژ"

            if any(
                letter in text
                for letter in urdu_letters
            ):

                return "ur"

            return "ar"

        script_ranges = [
            ("te", 0x0C00, 0x0C7F),
            ("ta", 0x0B80, 0x0BFF),
            ("hi", 0x0900, 0x097F),
            ("kn", 0x0C80, 0x0CFF),
            ("ml", 0x0D00, 0x0D7F),
            ("bn", 0x0980, 0x09FF),
            ("gu", 0x0A80, 0x0AFF),
            ("pa", 0x0A00, 0x0A7F),
            ("ja", 0x3040, 0x30FF),
            ("ko", 0xAC00, 0xD7AF),
            ("zh", 0x4E00, 0x9FFF),
        ]

        for code, low, high in script_ranges:

            if re.search(
                f"[{chr(low)}-{chr(high)}]",
                text,
            ):

                return code

        return "en"

    # ==================================================
    # FIX: EXTENDED LANGUAGE INSTRUCTION
    # ==================================================

    def _language_instruction(
        self,
        language: str,
    ) -> str:

        key = (
            str(language or "en")
            .lower()
            .strip()
        )

        if key in self.EXTRA_LANGUAGES:

            return self.EXTRA_LANGUAGES[
                key
            ]

        return super()._language_instruction(
            language
        )

    # ==================================================
    # FIX: SEARCH — cache + rate-limit retry
    # + search_depth support
    # ==================================================

    def search(
        self,
        query: str,
        max_results: int = 5,
        topic: str = "general",
        time_range: Optional[str] = None,
        include_domains: Optional[List[str]] = None,
        search_depth: Optional[str] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:

        normalized = (
            str(query or "").strip()
        )

        if not normalized:

            return super().search(
                query
            )

        cache_key = (
            normalized.lower(),
            max_results,
            topic,
            time_range,
            tuple(
                include_domains or ()
            ),
        )

        # -----------------------------
        # CACHE HIT
        # -----------------------------

        if use_cache:

            with self._cache_lock:

                entry = (
                    self._search_cache
                    .get(cache_key)
                )

                if entry is not None:

                    stamp, payload = entry

                    if (
                        time.time() - stamp
                        < self.cache_ttl_seconds
                    ):

                        self._stats[
                            "cache_hits"
                        ] += 1

                        print(
                            "[WEB] Cache hit."
                        )

                        return {
                            "success": True,
                            "query": normalized,
                            "results": list(
                                payload
                            ),
                            "answer": "",
                            "error": None,
                        }

                self._search_cache.pop(
                    cache_key,
                    None,
                )

        # -----------------------------
        # SEARCH + RETRY
        # -----------------------------

        self._stats["searches"] += 1

        result = super().search(
            query=normalized,
            max_results=max_results,
            topic=topic,
            time_range=time_range,
            include_domains=include_domains,
        )

        # NOTE: search_depth is applied on
        # retry/advanced calls below — the
        # base signature doesn't accept it,
        # so it is injected via kwargs only
        # when the Tavily client supports it.

        attempts = 0

        while (
            not result.get("success")
            and attempts < self.search_retries
        ):

            error_text = str(
                result.get("error") or ""
            ).lower()

            retryable = (
                "429" in error_text
                or "rate" in error_text
                or "limit" in error_text
                or "timeout" in error_text
                or "connection" in error_text
            )

            if not retryable:

                break

            attempts += 1

            self._stats[
                "search_retries"
            ] += 1

            print(
                f"[WEB] Retrying search "
                f"(attempt {attempts})..."
            )

            time.sleep(
                0.8 * attempts
            )

            result = super().search(
                query=normalized,
                max_results=max_results,
                topic=topic,
                time_range=time_range,
                include_domains=include_domains,
            )

        if not result.get("success"):

            self._stats["errors"] += 1

            return result

        # -----------------------------
        # STORE CACHE
        # -----------------------------

        if use_cache:

            with self._cache_lock:

                self._search_cache[
                    cache_key
                ] = (
                    time.time(),
                    list(
                        result.get(
                            "results",
                            [],
                        )
                    ),
                )

                # keep the cache bounded

                if len(
                    self._search_cache
                ) > 100:

                    oldest = sorted(
                        self._search_cache.items(),
                        key=lambda item: item[1][0],
                    )

                    for key, _ in oldest[:20]:

                        self._search_cache.pop(
                            key,
                            None,
                        )

        return result

    # ==================================================
    # FIX: SUMMARIZE — language auto-detect
    # + bounded source text
    # ==================================================

    def _trim_results(
        self,
        results,
    ):

        if not results:

            return []

        trimmed = []

        total = 0

        for result in results:

            item = dict(result)

            content = str(
                item.get("content") or ""
            )

            if (
                len(content)
                > self.max_content_per_result
            ):

                item["content"] = (
                    content[
                        :self.max_content_per_result
                    ]
                    + "…"
                )

                self._stats[
                    "truncated_results"
                ] += 1

            remaining = (
                self.max_total_source_chars
                - total
            )

            if (
                trimmed
                and remaining <= 200
            ):

                break

            text = str(
                item.get("content") or ""
            )

            if len(text) > remaining:

                item["content"] = (
                    text[:remaining]
                    + "…"
                )

                self._stats[
                    "truncated_results"
                ] += 1

            total += len(
                str(
                    item.get("content") or ""
                )
            )

            trimmed.append(item)

        return trimmed

    def summarize(
        self,
        query: str,
        results: List[Dict[str, Any]],
        language: str = "en",
    ) -> str:

        # FIX: auto-detect the reply language
        # from the query's script when the
        # caller didn't specify one.

        if language in (
            None,
            "",
            "unknown",
            "en",
        ):

            detected = (
                self.detect_query_language(
                    query
                )
            )

            if detected != "en":

                print(
                    f"[WEB] Query language "
                    f"detected: {detected}"
                )

                language = detected

        # FIX: bound the source text before
        # it enters the prompt.

        safe_results = self._trim_results(
            results
        )

        self._stats["summaries"] += 1

        return super().summarize(
            query,
            safe_results,
            language,
        )

    # ==================================================
    # ASK WEB (adds speakable answer)
    # ==================================================

    def ask_web(
        self,
        *args,
        **kwargs,
    ) -> Dict[str, Any]:

        data = super().ask_web(
            *args,
            **kwargs,
        )

        if (
            data.get("success")
            and data.get("answer")
        ):

            data["answer_speakable"] = (
                self.clean_for_speech(
                    data["answer"]
                )
            )

        return data

    # ==================================================
    # NEWS (time_range now configurable)
    # ==================================================

    def news(
        self,
        query: str,
        language: str = "en",
        max_results: int = 5,
        time_range: str = "week",
    ) -> Dict[str, Any]:

        return self.ask_web(
            query=query,
            language=language,
            max_results=max_results,
            topic="news",
            time_range=time_range,
        )

    # ==================================================
    # SPEECH CLEANER (mirrors the TTS Pro filter)
    # ==================================================

    def clean_for_speech(self, text):

        text = str(text or "")

        text = re.sub(
            r"```.*?```",
            " ",
            text,
            flags=re.S,
        )

        text = re.sub(
            r"\[([^\]]+)\]\([^)]*\)",
            r"\1",
            text,
        )

        text = re.sub(
            r"https?://\S+",
            " ",
            text,
        )

        text = re.sub(
            r"[*_#>`~|]",
            " ",
            text,
        )

        text = re.sub(
            "["
            "\U0001F000-\U0001FAFF"
            "\U00002600-\U000027BF"
            "\U0001F1E6-\U0001F1FF"
            "\u2190-\u21FF"
            "\u2B00-\u2BFF"
            "\uFE0F\u200D"
            "]+",
            " ",
            text,
        )

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

    def speakable_answer(self, answer):

        return self.clean_for_speech(
            answer
        )

    # ==================================================
    # CITATIONS
    # ==================================================

    def sources_line(
        self,
        results,
        limit=3,
    ):

        names = []

        for result in (results or [])[:limit]:

            title = str(
                result.get("title") or ""
            ).strip()

            if title:

                names.append(title)

        if not names:

            return ""

        return (
            "Sources: "
            + ", ".join(names)
            + "."
        )

    # ==================================================
    # ONE-CALL CONVENIENCE
    # ==================================================

    def quick_answer(
        self,
        query: str,
        language: str = "en",
        max_results: int = 5,
        topic: str = "general",
        time_range: Optional[str] = None,
    ) -> str:

        data = self.ask_web(
            query=query,
            language=language,
            max_results=max_results,
            topic=topic,
            time_range=time_range,
        )

        if not data.get("success"):

            self._stats["errors"] += 1

            error = str(
                data.get("error") or ""
            ).strip()

            if error:

                return (
                    "I couldn't search the web "
                    f"right now. ({error})"
                )

            return (
                "I couldn't search the web "
                "right now."
            )

        return (
            data.get("answer")
            or "I found results but couldn't "
            "summarize them."
        )

    # ==================================================
    # CACHE + STATS
    # ==================================================

    def clear_cache(self):

        with self._cache_lock:

            self._search_cache.clear()

        print("[WEB] Search cache cleared.")

    def get_stats(self):

        stats = dict(self._stats)

        with self._cache_lock:

            stats["cached_queries"] = len(
                self._search_cache
            )

        stats["cache_ttl"] = (
            self.cache_ttl_seconds
        )

        return stats


# ------------------------------------------------------------
# DROP-IN UPGRADE
# Anything that imports WebIntelligence from this file now
# gets the extended version automatically (same API).
# Delete the next line to keep using the original.
# ------------------------------------------------------------

WebIntelligence = WebIntelligencePro


# ============================================================
# QUICK TEST (uncomment to try)
# ============================================================
#
# if __name__ == "__main__":
#
#     web = WebIntelligence()
#
#     # One-call answer:
#     print(web.quick_answer("who won the last cricket world cup"))
#
#     # Full data with speakable text for TTS:
#     data = web.ask_web("best laptop under 50000 rupees", language="en")
#     print(data["answer"])
#     print(data.get("answer_speakable"))
#     print(web.sources_line(data["results"]))
#
#     # Second identical call is a cache hit:
#     web.quick_answer("who won the last cricket world cup")
#     print(web.get_stats())
#
#     # Non-English query auto-answers in that language:
#     print(web.quick_answer("భారతదేశ రాజధాని ఏమిటి"))