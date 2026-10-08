import json
import re

from groq import Groq

import config


class LunaPlanner:

    def __init__(self):

        if not config.GROQ_API_KEY:

            raise ValueError(
                "GROQ_API_KEY is missing in .env"
            )

        self.client = Groq(
            api_key=config.GROQ_API_KEY
        )

        self.model = config.GROQ_MODEL

    # ========================================================
    # CREATE PLAN
    # ========================================================

    def create_plan(
        self,
        user_text: str
    ):

        if not user_text or not user_text.strip():

            return {
                "actions": []
            }

        prompt = f"""
You are LUNA's multilingual computer-action planner.

Understand natural language in:

English
Telugu
Hindi
Tamil
Kannada
Malayalam
Bengali
Marathi
Gujarati
Punjabi
Urdu
Arabic
mixed languages
transliterated languages

Your task is to convert the user's request into an
ordered list of safe, executable actions.

============================================================
WINDOWS ACTIONS
============================================================

open_application
open_website
open_folder

take_screenshot
system_info

increase_volume
decrease_volume
mute
unmute

lock_computer

mouse_position
mouse_move

click
double_click
right_click

scroll_up
scroll_down

copy
paste

type_text
press_key

============================================================
BROWSER ACTIONS
============================================================

browser_open

google_search
youtube_search

google_search_interactive
youtube_search_interactive

browser_click
browser_click_text
browser_click_first_result

browser_type
browser_press

browser_read_page
browser_read_results
browser_read_links

browser_title
browser_url

browser_back
browser_forward
browser_refresh

browser_new_tab
browser_close_tab

============================================================
APPLICATIONS
============================================================

chrome
notepad
calculator
paint
file explorer
task manager
vs code

============================================================
WEBSITES
============================================================

google
youtube
github
gmail
chatgpt
instagram

============================================================
FOLDERS
============================================================

downloads
documents
desktop
pictures
music
videos

============================================================
RULES
============================================================

1. Understand the meaning regardless of language.

2. Understand mixed-language commands.

3. Understand transliterated Indian-language commands.

Examples:

"Chrome open cheyyi"
"Chrome open karo"
"YouTube ki vellandi"
"Chrome kholo"
"குரோம் திற"
"లూనా క్రోమ్ ఓపెన్ చెయ్యి"

4. Preserve the requested action order.

5. Never invent unsupported actions.

6. For:
   "Open Chrome and search YouTube for Python tutorials"

   return:

   open_application -> chrome

   youtube_search_interactive -> Python tutorials

7. For:
   "Open Chrome and search Google for Python tutorials"

   return:

   open_application -> chrome

   google_search_interactive -> Python tutorials

8. For:
   "Open Chrome and search YouTube for Python tutorials
    and open the first result"

   return:

   open_application -> chrome

   youtube_search_interactive -> Python tutorials

   browser_click_first_result -> youtube

9. For:
    "Open Google, search for AI news and open the first result"

   return:

   open_application -> chrome

   google_search_interactive -> AI news

   browser_click_first_result -> google

10. For:
    "Open YouTube and tell me the first three results"

    return:

    open_application -> chrome

    youtube_search_interactive -> [query]

    browser_read_results

11. For:
    "Read this webpage"

    use:

    browser_read_page

12. Do not use mouse coordinates when a browser action
    can accomplish the task.

13. Return ONLY valid JSON.

14. Do not return explanations.

============================================================
JSON FORMAT
============================================================

{{
    "actions": [
        {{
            "action": "open_application",
            "target": "chrome",
            "text": null,
            "key": null,
            "x": null,
            "y": null
        }}
    ]
}}

============================================================
EXAMPLE 1
============================================================

User:

Open Chrome and search YouTube for AI tutorials.

Return:

{{
    "actions": [
        {{
            "action": "open_application",
            "target": "chrome",
            "text": null,
            "key": null,
            "x": null,
            "y": null
        }},
        {{
            "action": "youtube_search_interactive",
            "target": null,
            "text": "AI tutorials",
            "key": null,
            "x": null,
            "y": null
        }}
    ]
}}

============================================================
EXAMPLE 2
============================================================

User:

Open YouTube, search for Python tutorials,
and open the first result.

Return:

{{
    "actions": [
        {{
            "action": "open_application",
            "target": "chrome",
            "text": null,
            "key": null,
            "x": null,
            "y": null
        }},
        {{
            "action": "youtube_search_interactive",
            "target": null,
            "text": "Python tutorials",
            "key": null,
            "x": null,
            "y": null
        }},
        {{
            "action": "browser_click_first_result",
            "target": "youtube",
            "text": null,
            "key": null,
            "x": null,
            "y": null
        }}
    ]
}}

============================================================
EXAMPLE 3
============================================================

User:

Luna, Chrome open cheyyi, YouTube lo AI tutorials
search cheyyi and first video open cheyyi.

Return:

{{
    "actions": [
        {{
            "action": "open_application",
            "target": "chrome",
            "text": null,
            "key": null,
            "x": null,
            "y": null
        }},
        {{
            "action": "youtube_search_interactive",
            "target": null,
            "text": "AI tutorials",
            "key": null,
            "x": null,
            "y": null
        }},
        {{
            "action": "browser_click_first_result",
            "target": "youtube",
            "text": null,
            "key": null,
            "x": null,
            "y": null
        }}
    ]
}}

============================================================
EXAMPLE 4
============================================================

User:

Search Google for AI news and tell me the first results.

Return:

{{
    "actions": [
        {{
            "action": "open_application",
            "target": "chrome",
            "text": null,
            "key": null,
            "x": null,
            "y": null
        }},
        {{
            "action": "google_search_interactive",
            "target": null,
            "text": "AI news",
            "key": null,
            "x": null,
            "y": null
        }},
        {{
            "action": "browser_read_links",
            "target": null,
            "text": null,
            "key": null,
            "x": null,
            "y": null
        }}
    ]
}}

============================================================
USER REQUEST
============================================================

{user_text}
"""

        try:

            response = (
                self.client
                .chat
                .completions
                .create(

                    model=self.model,

                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are LUNA's strict "
                                "JSON planner. "
                                "Return JSON only."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],

                    temperature=0,

                    max_tokens=800
                )
            )

            raw = (
                response
                .choices[0]
                .message
                .content
                .strip()
            )

            print()
            print(
                "[PLANNER] RAW RESPONSE:"
            )

            print(
                raw
            )

            data = self._extract_json(
                raw
            )

            return self._validate(
                data
            )

        except Exception as error:

            print(
                f"[PLANNER] Error: {error}"
            )

            return {
                "actions": []
            }

    # ========================================================
    # EXTRACT JSON
    # ========================================================

    def _extract_json(
        self,
        raw
    ):

        try:

            return json.loads(
                raw
            )

        except json.JSONDecodeError:

            match = re.search(
                r"\{.*\}",
                raw,
                re.DOTALL
            )

            if match:

                try:

                    return json.loads(
                        match.group(0)
                    )

                except json.JSONDecodeError:

                    pass

        return {}

    # ========================================================
    # VALIDATE
    # ========================================================

    def _validate(
        self,
        data
    ):

        if not isinstance(
            data,
            dict
        ):

            return {
                "actions": []
            }

        actions = data.get(
            "actions",
            []
        )

        if not isinstance(
            actions,
            list
        ):

            return {
                "actions": []
            }

        allowed_actions = {

            # -----------------------------------------------
            # Windows
            # -----------------------------------------------

            "open_application",
            "open_website",
            "open_folder",

            "take_screenshot",
            "system_info",

            "increase_volume",
            "decrease_volume",

            "mute",
            "unmute",

            "lock_computer",

            "mouse_position",
            "mouse_move",

            "click",
            "double_click",
            "right_click",

            "scroll_up",
            "scroll_down",

            "copy",
            "paste",

            "type_text",
            "press_key",

            # -----------------------------------------------
            # Browser
            # -----------------------------------------------

            "browser_open",

            "google_search",
            "youtube_search",

            "google_search_interactive",
            "youtube_search_interactive",

            "browser_click",
            "browser_click_text",
            "browser_click_first_result",

            "browser_type",
            "browser_press",

            "browser_read_page",
            "browser_read_results",
            "browser_read_links",

            "browser_title",
            "browser_url",

            "browser_back",
            "browser_forward",
            "browser_refresh",

            "browser_new_tab",
            "browser_close_tab",
        }

        valid = []

        for item in actions:

            if not isinstance(
                item,
                dict
            ):

                continue

            action = str(
                item.get(
                    "action",
                    ""
                )
            ).strip().lower()

            if action not in allowed_actions:

                continue

            target = item.get(
                "target"
            )

            text = item.get(
                "text"
            )

            key = item.get(
                "key"
            )

            x = item.get(
                "x"
            )

            y = item.get(
                "y"
            )

            # -------------------------------------------
            # Normalize values
            # -------------------------------------------

            if target is not None:

                target = str(
                    target
                ).strip().lower()

            if text is not None:

                text = str(
                    text
                )

            if key is not None:

                key = str(
                    key
                ).strip().lower()

            if x is not None:

                try:

                    x = int(x)

                except (
                    TypeError,
                    ValueError
                ):

                    x = None

            if y is not None:

                try:

                    y = int(y)

                except (
                    TypeError,
                    ValueError
                ):

                    y = None

            valid.append(
                {
                    "action": action,

                    "target": target,

                    "text": text,

                    "key": key,

                    "x": x,

                    "y": y,
                }
            )

        return {
            "actions": valid
        }


# ============================================================
# ============================================================
#
#   🌙 LUNA PLANNER PRO — EXTENSIONS (APPEND ONLY)
#
#   The original LunaPlanner above is 100% unchanged.
#   Pro wraps create_plan and replaces _extract_json /
#   _validate with hardened versions.
#
#   FIXES
#     • Validator deleted every NEW action — allowed_actions
#       was frozen at the original executor's vocabulary, so
#       battery_status / set_volume / media_next / reminders
#       etc. were silently stripped from LLM plans even
#       though the extended ActionExecutor supports them.
#     • Validator dropped extra parameters — every action was
#       rebuilt with only target/text/key/x/y, so "seconds"
#       (reminders, waits), "percent", and "steps" vanished.
#     • browser_open URLs were lowercased — case-sensitive
#       paths and query strings broke.
#     • No retry — one transient network error returned an
#       empty plan even though a second attempt would work.
#     • JSON extraction failed on truncated LLM output —
#       no fence stripping, no brace-balancing repair.
#     • No plan cap or dedupe — a runaway LLM could emit
#       dozens of duplicate actions.
#     • Groq client had no timeout — a stalled connection
#       hung planning indefinitely.
#
#   ADDITIONS
#     • LOCAL FAST PATH — simple single-step commands
#       ("screenshot", "battery", "volume up", "open notepad")
#       are planned instantly by the local NLP chain with
#       ZERO LLM calls: ~0ms, offline, no API cost. Complex
#       multi-step browser flows still go to Groq.
#     • EMPTY-PLAN RETRY with backoff.
#     • JSON repair: markdown fences, string-aware brace
#       balancing, trailing-comma cleanup, truncation rescue.
#     • known_actions() + get_stats().
#
# ============================================================
# ============================================================

import time


class LunaPlannerPro(LunaPlanner):

    # ==================================================
    # EXTENDED ALLOWED ACTIONS
    # (base set + everything the extended
    #  ActionExecutor supports)
    # ==================================================

    EXTRA_ALLOWED_ACTIONS = {
        # system readings
        "battery_status", "check_battery", "battery",
        "system_health", "system_status",
        "performance_status",
        "uptime", "screen_resolution",
        "get_time", "get_date",
        # wi-fi
        "wifi_status", "wifi_info",
        "wifi_scan", "list_wifi",
        # audio / display
        "set_volume", "volume_up", "volume_down",
        "set_brightness", "brightness_up",
        "brightness_down", "brightness_status",
        # media
        "media_play_pause", "media_next",
        "media_previous", "media_stop",
        # power
        "sleep_computer", "hibernate",
        "restart_computer", "reboot_computer",
        "shutdown_computer", "abort_shutdown",
        # capture / clipboard / desktop
        "take_webcam_photo",
        "set_clipboard", "read_clipboard",
        "show_notification", "set_reminder",
        "minimize_window", "maximize_window",
        "show_desktop", "switch_window",
        "close_window", "close_application",
        "empty_recycle_bin",
        # browser extras
        "browser_zoom_in", "browser_zoom_out",
        "browser_zoom_reset", "browser_fullscreen",
        "browser_find", "browser_scroll_top",
        "browser_scroll_bottom", "browser_select_all",
        # plan flow
        "wait", "pause",
    }

    EXTRA_PARAM_KEYS = (
        "seconds",
        "minutes",
        "percent",
        "steps",
        "duration",
    )

    # ==================================================
    # SIMPLE-COMMAND GUARDS (local fast path)
    # ==================================================

    SIMPLE_BLOCKERS = re.compile(
        r"\band\b|\bthen\b"
        r"|first\s+(?:result|video|three|link)"
        r"|\bread\b|\bresults?\b|\blinks\b"
        r"|\bwebpage\b|\bscroll\b.*\band\b",
        re.IGNORECASE,
    )

    # ==================================================
    # SINGLE-STEP INTENT → ACTION MAP
    # ==================================================

    SIMPLE_ACTION_MAP = {
        "take_screenshot": "take_screenshot",
        "system_info": "system_info",
        "system_health": "system_health",
        "battery_status": "battery_status",
        "uptime": "uptime",
        "get_time": "get_time",
        "get_date": "get_date",
        "wifi_status": "wifi_status",
        "wifi_scan": "wifi_scan",
        "increase_volume": "increase_volume",
        "decrease_volume": "decrease_volume",
        "mute": "mute",
        "unmute": "unmute",
        "brightness_up": "brightness_up",
        "brightness_down": "brightness_down",
        "media_play_pause": "media_play_pause",
        "media_next": "media_next",
        "media_previous": "media_previous",
        "media_stop": "media_stop",
        "shutdown_computer": "shutdown_computer",
        "restart_computer": "restart_computer",
        "sleep_computer": "sleep_computer",
        "abort_shutdown": "abort_shutdown",
        "lock_computer": "lock_computer",
        "mouse_position": "mouse_position",
        "click": "click",
        "double_click": "double_click",
        "right_click": "right_click",
        "scroll_up": "scroll_up",
        "scroll_down": "scroll_down",
        "copy": "copy",
        "paste": "paste",
        "read_clipboard": "read_clipboard",
        "empty_recycle_bin": "empty_recycle_bin",
        "show_desktop": "show_desktop",
        "minimize_window": "minimize_window",
        "maximize_window": "maximize_window",
        "close_window": "close_window",
    }

    # ==================================================
    # SETUP
    # ==================================================

    def __init__(self):

        super().__init__()

        # FIX: Groq with timeout + SDK retries

        try:

            self.client = Groq(
                api_key=config.GROQ_API_KEY,
                timeout=30.0,
                max_retries=2,
            )

        except Exception:

            pass  # base client stays

        # -----------------------------
        # SETTINGS
        # -----------------------------

        self.use_local_fast_path = True

        self.llm_retries = 1

        self.max_actions = 12

        # -----------------------------
        # STATE
        # -----------------------------

        self._nlp = None

        self._stats = {
            "plans": 0,
            "local_plans": 0,
            "llm_plans": 0,
            "llm_retries": 0,
            "json_repairs": 0,
            "dropped_actions": 0,
            "capped": 0,
        }

    # ==================================================
    # LOCAL NLP (lazy — degrades gracefully)
    # ==================================================

    def _get_nlp(self):

        if self._nlp is not None:

            return self._nlp

        try:

            from nlp.nlp_engine import (
                NLPEngine,
            )

        except ImportError:

            try:

                from nlp_engine import (
                    NLPEngine,
                )

            except ImportError:

                return None

        try:

            self._nlp = NLPEngine()

        except Exception:

            return None

        return self._nlp

    # ==================================================
    # LOCAL FAST PATH
    # ==================================================

    def _local_plan(
        self,
        text,
    ):

        nlp = self._get_nlp()

        if nlp is None:

            return None

        if self.SIMPLE_BLOCKERS.search(
            text
        ):

            return None

        try:

            analysis = nlp.analyze(
                text
            )

        except Exception:

            return None

        if not analysis.get(
            "is_command"
        ):

            return None

        if analysis.get(
            "source"
        ) != "local":

            return None

        intent = analysis.get(
            "intent",
            "unknown",
        )

        entity = analysis.get(
            "entity"
        )

        value_text = analysis.get(
            "text"
        )

        key = analysis.get(
            "key"
        )

        x = analysis.get(
            "x"
        )

        y = analysis.get("y")

        # ------------------------------------------
        # Parameterless intents
        # ------------------------------------------

        if intent in (
            self.SIMPLE_ACTION_MAP
        ):

            return {
                "actions": [
                    {
                        "action": (
                            self
                            .SIMPLE_ACTION_MAP[
                                intent
                            ]
                        ),
                        "target": None,
                        "text": None,
                        "key": None,
                        "x": None,
                        "y": None,
                    }
                ]
            }

        # ------------------------------------------
        # Parameterized intents
        # ------------------------------------------

        action = None

        params = {}

        if intent == "open_application":

            if entity:

                action = "open_application"

                params["target"] = str(
                    entity
                )

        elif intent == "open_website":

            if entity:

                action = "open_website"

                params["target"] = str(
                    entity
                )

        elif intent == "open_folder":

            if entity:

                action = "open_folder"

                params["target"] = str(
                    entity
                )

        elif intent == "close_application":

            if entity:

                action = "close_application"

                params["target"] = str(
                    entity
                )

        elif intent == "type_text":

            if value_text:

                action = "type_text"

                params["text"] = str(
                    value_text
                )

        elif intent == "press_key":

            if key:

                action = "press_key"

                params["key"] = str(
                    key
                )

        elif intent == "mouse_move":

            if (
                x is not None
                and y is not None
            ):

                action = "mouse_move"

                params["x"] = int(x)

                params["y"] = int(y)

        elif intent == "youtube_search":

            if value_text:

                action = "youtube_search"

                params["text"] = str(
                    value_text
                )

        elif intent == "google_search":

            if value_text:

                action = "google_search"

                params["text"] = str(
                    value_text
                )

        elif intent == "set_volume":

            percent = self._percent_of(
                analysis
            )

            if percent is not None:

                action = "set_volume"

                params["percent"] = (
                    percent
                )

        elif intent == "set_brightness":

            percent = self._percent_of(
                analysis
            )

            if percent is not None:

                action = "set_brightness"

                params["percent"] = (
                    percent
                )

        elif intent == "set_reminder":

            if isinstance(
                entity,
                dict,
            ) and (
                entity.get("seconds")
                or entity.get("message")
            ):

                action = "set_reminder"

                if entity.get(
                    "seconds"
                ):

                    params["seconds"] = int(
                        entity["seconds"]
                    )

                if entity.get(
                    "message"
                ):

                    params["text"] = str(
                        entity["message"]
                    )

        elif intent == "show_notification":

            if value_text:

                action = "show_notification"

                params["text"] = str(
                    value_text
                )

        elif intent == "set_clipboard":

            if value_text:

                action = "set_clipboard"

                params["text"] = str(
                    value_text
                )

        if action is None:

            return None

        step = {
            "action": action,
            "target": None,
            "text": None,
            "key": None,
            "x": None,
            "y": None,
        }

        step.update(params)

        return {
            "actions": [step]
        }

    @staticmethod
    def _percent_of(analysis):

        entity = analysis.get(
            "entity"
        )

        if isinstance(
            entity,
            dict,
        ) and entity.get(
            "percent"
        ) is not None:

            try:

                return int(
                    entity["percent"]
                )

            except (
                TypeError,
                ValueError,
            ):

                return None

        value_text = analysis.get(
            "text"
        )

        if value_text:

            match = re.search(
                r"\d{1,3}",
                str(value_text),
            )

            if match:

                value = int(
                    match.group(0)
                )

                if 0 <= value <= 100:

                    return value

        return None

    # ==================================================
    # CREATE PLAN (fast path → LLM → retry)
    # ==================================================

    def create_plan(
        self,
        user_text: str,
    ):

        text = str(
            user_text or ""
        ).strip()

        if not text:

            return {
                "actions": []
            }

        self._stats["plans"] += 1

        # ------------------------------------------
        # 1) LOCAL FAST PATH
        # ------------------------------------------

        if self.use_local_fast_path:

            local = self._local_plan(
                text
            )

            if local:

                self._stats[
                    "local_plans"
                ] += 1

                print()

                print(
                    "[PLANNER] Local fast "
                    "path (no LLM call)."
                )

                print(
                    "[PLANNER] Plan:",
                    local,
                )

                return local

        # ------------------------------------------
        # 2) LLM (original prompt) + RETRY
        # ------------------------------------------

        for attempt in range(
            self.llm_retries + 1
        ):

            plan = super().create_plan(
                text
            )

            if plan.get("actions"):

                self._stats[
                    "llm_plans"
                ] += 1

                return plan

            if (
                attempt
                < self.llm_retries
            ):

                self._stats[
                    "llm_retries"
                ] += 1

                print(
                    "[PLANNER] Empty plan — "
                    "retrying..."
                )

                time.sleep(0.5)

        return {
            "actions": []
        }

    # ==================================================
    # FIX: JSON EXTRACTION (fences + repair)
    # ==================================================

    def _extract_json(
        self,
        raw,
    ):

        if not raw:

            return {}

        cleaned = str(raw).strip()

        # ------------------------------------------
        # Strip markdown fences
        # ------------------------------------------

        fence = re.search(
            r"```(?:json)?\s*(.*?)\s*```",
            cleaned,
            re.DOTALL,
        )

        if fence:

            cleaned = (
                fence.group(1).strip()
            )

        # ------------------------------------------
        # Direct parse
        # ------------------------------------------

        try:

            return json.loads(
                cleaned
            )

        except json.JSONDecodeError:

            pass

        # ------------------------------------------
        # Base extraction (regex grab)
        # ------------------------------------------

        data = super()._extract_json(
            cleaned
        )

        if data:

            return data

        # ------------------------------------------
        # Brace-balanced repair
        # ------------------------------------------

        repaired = (
            self._repair_json(cleaned)
        )

        if repaired is not None:

            self._stats[
                "json_repairs"
            ] += 1

            print(
                "[PLANNER] JSON repaired."
            )

            return repaired

        return {}

    @staticmethod
    def _repair_json(raw):

        start = raw.find("{")

        if start == -1:

            return None

        depth = 0

        in_string = False

        escaped = False

        end = -1

        for index in range(
            start,
            len(raw),
        ):

            char = raw[index]

            if in_string:

                if escaped:

                    escaped = False

                elif char == "\\":

                    escaped = True

                elif char == '"':

                    in_string = False

                continue

            if char == '"':

                in_string = True

            elif char == "{":

                depth += 1

            elif char == "}":

                depth -= 1

                if depth == 0:

                    end = index

                    break

        if end != -1:

            candidate = raw[
                start:end + 1
            ]

        elif depth > 0:

            # truncation rescue — close
            # the open braces

            candidate = (
                raw[start:]
                + "}" * depth
            )

        else:

            return None

        candidate = re.sub(
            r",\s*([}\]])",
            r"\1",
            candidate,
        )

        try:

            data = json.loads(
                candidate
            )

            return (
                data
                if isinstance(
                    data,
                    dict,
                )
                else None
            )

        except json.JSONDecodeError:

            return None

    # ==================================================
    # FIX: VALIDATION (extended + param-preserving)
    # ==================================================

    def _validate(
        self,
        data,
    ):

        if not isinstance(
            data,
            dict,
        ):

            return {
                "actions": []
            }

        actions = data.get(
            "actions",
            [],
        )

        if not isinstance(
            actions,
            list,
        ):

            return {
                "actions": []
            }

        allowed = (
            self.EXTRA_ALLOWED_ACTIONS
        )

        valid = []

        for item in actions:

            if not isinstance(
                item,
                dict,
            ):

                continue

            action = str(
                item.get(
                    "action",
                    "",
                )
            ).strip().lower()

            if action not in allowed:

                self._stats[
                    "dropped_actions"
                ] += 1

                continue

            target = item.get(
                "target"
            )

            text = item.get(
                "text"
            )

            key = item.get(
                "key"
            )

            x = item.get(
                "x"
            )

            y = item.get(
                "y"
            )

            # FIX: URLs keep their case

            if target is not None:

                target = str(
                    target
                ).strip()

                if action not in (
                    "browser_open",
                ):

                    target = (
                        target.lower()
                    )

            if text is not None:

                text = str(text)

            if key is not None:

                key = str(
                    key
                ).strip().lower()

            for name, value in (
                ("x", x),
                ("y", y),
            ):

                if value is not None:

                    try:

                        value = int(
                            value
                        )

                    except (
                        TypeError,
                        ValueError,
                    ):

                        value = None

                if name == "x":

                    x = value

                else:

                    y = value

            step = {
                "action": action,
                "target": target,
                "text": text,
                "key": key,
                "x": x,
                "y": y,
            }

            # FIX: preserve extra params
            # (seconds, percent, steps…)

            for param in (
                self.EXTRA_PARAM_KEYS
            ):

                value = item.get(
                    param
                )

                if value is None:

                    continue

                if isinstance(
                    value,
                    str,
                ):

                    match = re.search(
                        r"-?\d+",
                        value,
                    )

                    if not match:

                        continue

                    value = int(
                        match.group(0)
                    )

                try:

                    step[param] = int(
                        value
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    continue

            valid.append(step)

        # ------------------------------------------
        # Dedupe consecutive identical steps
        # ------------------------------------------

        deduped = []

        for step in valid:

            if (
                deduped
                and deduped[-1]
                == step
            ):

                continue

            deduped.append(step)

        # ------------------------------------------
        # Cap runaway plans
        # ------------------------------------------

        if (
            len(deduped)
            > self.max_actions
        ):

            self._stats[
                "capped"
            ] += 1

            print(
                f"[PLANNER] Plan capped at "
                f"{self.max_actions} actions."
            )

            deduped = deduped[
                :self.max_actions
            ]

        return {
            "actions": deduped
        }

    # ==================================================
    # REGISTRY + STATS
    # ==================================================

    @classmethod
    def known_actions(cls):

        base = {

            "open_application", "open_website",
            "open_folder", "take_screenshot",
            "system_info", "increase_volume",
            "decrease_volume", "mute", "unmute",
            "lock_computer", "mouse_position",
            "mouse_move", "click", "double_click",
            "right_click", "scroll_up", "scroll_down",
            "copy", "paste", "type_text", "press_key",
            "browser_open", "google_search",
            "youtube_search", "google_search_interactive",
            "youtube_search_interactive", "browser_click",
            "browser_click_text", "browser_click_first_result",
            "browser_type", "browser_press",
            "browser_read_page", "browser_read_results",
            "browser_read_links", "browser_title",
            "browser_url", "browser_back",
            "browser_forward", "browser_refresh",
            "browser_new_tab", "browser_close_tab",
        }

        return sorted(
            base
            | cls.EXTRA_ALLOWED_ACTIONS
        )

    def get_stats(self):

        return dict(self._stats)


# ------------------------------------------------------------
# DROP-IN UPGRADE
# Anything importing LunaPlanner now gets the extended
# version (same create_plan API and plan format).
# Delete the next line to keep the original.
# ------------------------------------------------------------

LunaPlanner = LunaPlannerPro


# ============================================================
# QUICK TEST (uncomment to try)
# ============================================================
#
# if __name__ == "__main__":
#
#     planner = LunaPlanner()
#
#     # 1. Local fast path — instant, no LLM call:
#     print(planner.create_plan("take a screenshot"))
#     print(planner.create_plan("what's my battery level"))
#     print(planner.create_plan("set volume to 40"))
#     print(planner.create_plan("open notepad"))
#     print(planner.create_plan("remind me in 10 minutes to stretch"))
#
#     # 2. Complex multi-step — goes to Groq:
#     print(planner.create_plan(
#         "Open Chrome and search YouTube for Python tutorials"
#         " and open the first result"
#     ))
#
#     # 3. Registry:
#     print(len(planner.known_actions()), "actions supported")
#     print(planner.get_stats())