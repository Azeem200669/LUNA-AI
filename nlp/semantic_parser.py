import json
import re

from groq import Groq

import config


class MultilingualSemanticParser:

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
    # PARSE
    # ========================================================

    def parse(
        self,
        text: str
    ) -> dict:

        prompt = f"""
You are LUNA's multilingual computer-command parser.

Understand the user's meaning regardless of language.

Supported intents:

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
click
double_click
right_click
scroll_up
scroll_down
copy
paste
type_text
press_key
unknown

Supported application targets:

chrome
notepad
calculator
paint
file explorer
task manager
vs code

Supported website targets:

google
youtube
github
gmail
chatgpt
instagram

Supported folder targets:

downloads
documents
desktop
pictures
music
videos

Important:
- Understand Telugu, Hindi, Tamil, Kannada, Malayalam,
  Bengali, Marathi, Gujarati, Punjabi, Urdu, Arabic,
  English and mixed-language speech.
- Understand transliterated speech such as:
  "Chrome open cheyyi"
  "Chrome open karo"
  "YouTube ki vellandi"
- Understand code-switching and mixed-language sentences.
- Extract the actual intent and target.
- Do not translate the command for the user.
- Return ONLY valid JSON.
- Do not use markdown.
- Do not add explanations.

JSON format:

{{
    "intent": "open_application",
    "target": "chrome",
    "text": null,
    "key": null,
    "x": null,
    "y": null,
    "confidence": 0.98
}}

For type_text:
{{
    "intent": "type_text",
    "target": null,
    "text": "hello luna",
    "key": null,
    "x": null,
    "y": null,
    "confidence": 0.98
}}

For move mouse:
{{
    "intent": "mouse_move",
    "target": null,
    "text": null,
    "key": null,
    "x": 500,
    "y": 400,
    "confidence": 0.98
}}

User message:

{text}
"""

        try:

            response = self.client.chat.completions.create(

                model=self.model,

                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a strict JSON "
                            "computer-command parser."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=0,

                max_tokens=250
            )

            raw = (
                response
                .choices[0]
                .message
                .content
                .strip()
            )

            result = self._extract_json(
                raw
            )

            return self._validate(
                result
            )

        except Exception as error:

            print(
                f"[NLP] Semantic parser error: "
                f"{error}"
            )

            return {
                "intent": "unknown",
                "target": None,
                "text": None,
                "key": None,
                "x": None,
                "y": None,
                "confidence": 0.0,
            }

    # ========================================================
    # EXTRACT JSON
    # ========================================================

    def _extract_json(
        self,
        raw: str
    ) -> dict:

        # Direct JSON

        try:

            return json.loads(
                raw
            )

        except json.JSONDecodeError:
            pass

        # Search JSON inside response

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
    ) -> dict:

        if not isinstance(
            data,
            dict
        ):

            return {
                "intent": "unknown",
                "target": None,
                "text": None,
                "key": None,
                "x": None,
                "y": None,
                "confidence": 0.0,
            }

        intent = str(
            data.get(
                "intent",
                "unknown"
            )
        ).strip().lower()

        target = data.get(
            "target"
        )

        typed_text = data.get(
            "text"
        )

        key = data.get(
            "key"
        )

        x = data.get(
            "x"
        )

        y = data.get(
            "y"
        )

        try:

            confidence = float(
                data.get(
                    "confidence",
                    0.0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            confidence = 0.0

        return {
            "intent": intent,
            "target": target,
            "text": typed_text,
            "key": key,
            "x": x,
            "y": y,
            "confidence": confidence,
        }


# ============================================================
# ============================================================
#
#   🌙 LUNA SEMANTIC PARSER PRO — EXTENSIONS (APPEND ONLY)
#
#   The original MultilingualSemanticParser above is 100%
#   unchanged. Pro owns parse() end-to-end (the fixes live
#   inside the prompt/LLM/validation flow, which delegation
#   cannot reach) and keeps the exact result schema.
#
#   FIXES
#     • Prompt inconsistency — the JSON example shows
#       "mouse_move" but the supported-intents list omits
#       it, so the model hesitated on "move the mouse to
#       500, 400". Extended prompt lists mouse_move.
#     • Hallucinated intents passed validation — any
#       invented intent ("play_music", "order_pizza")
#       flowed through with confidence 0.98 and became
#       is_command=True downstream, only to die later as
#       "Unsupported action". Pro whitelists intents.
#     • Unclamped confidence — the LLM could return 1.5
#       or -0.2; Pro clamps to [0, 1].
#     • Untyped x/y — the model may return "500" as a
#       string; the base passed it through, breaking
#       mouse_move(int, int). Pro coerces to int.
#     • Empty text still triggered an LLM call — parse("")
#       burned an API round-trip to parse nothing.
#     • No timeout/retry on the Groq client — a stalled
#       connection hung parsing (same fix as planner/web).
#     • Fragile JSON extraction — markdown fences and
#       truncated output failed; no repair.
#     • No cache — the same repeated utterance paid the
#       LLM every time.
#
#   ADDITIONS
#     • Extended intent vocabulary — the parser can now
#       return every intent the extended ActionExecutor
#       understands (battery, volume %, media, power,
#       reminders, searches, window management…) for
#       MULTILINGUAL phrasings the local rules miss.
#     • Transliteration fast path — "chrome open cheyyi",
#       "youtube ki vellandi", "notepad kholo" parse
#       locally in ~0ms with zero LLM cost (guarded
#       against negation and long sentences).
#     • Local fallback — if the LLM is unreachable, the
#       Pro classifier produces a best-effort result
#       instead of a bare unknown.
#     • Bounded cache + get_stats().
#
# ============================================================
# ============================================================

import time


class MultilingualSemanticParserPro(MultilingualSemanticParser):

    # ==================================================
    # EXTENDED INTENT VOCABULARY
    # (original set + everything the extended
    #  ActionExecutor supports)
    # ==================================================

    BASE_INTENTS = {
        "open_application", "open_website", "open_folder",
        "take_screenshot", "system_info",
        "increase_volume", "decrease_volume",
        "mute", "unmute", "lock_computer",
        "mouse_position", "mouse_move",
        "click", "double_click", "right_click",
        "scroll_up", "scroll_down",
        "copy", "paste", "type_text", "press_key",
        "unknown",
    }

    EXTRA_INTENTS = {
        "close_application",
        "take_webcam_photo",
        "system_health", "battery_status",
        "get_time", "get_date", "uptime",
        "wifi_status", "wifi_scan",
        "set_volume", "set_brightness",
        "brightness_up", "brightness_down",
        "media_play_pause", "media_next",
        "media_previous", "media_stop",
        "sleep_computer", "restart_computer",
        "shutdown_computer", "abort_shutdown",
        "set_clipboard", "read_clipboard",
        "set_reminder", "show_notification",
        "empty_recycle_bin",
        "minimize_window", "maximize_window",
        "show_desktop", "close_window",
        "youtube_search", "google_search",
        "wait", "pause",
    }

    ALLOWED_INTENTS = (
        BASE_INTENTS | EXTRA_INTENTS
    )

    # ==================================================
    # TRANSLITERATION FAST PATH
    # ==================================================

    TARGET_MAP = {
        # apps
        "google chrome": ("app", "chrome"),
        "chrome": ("app", "chrome"),
        "notepad": ("app", "notepad"),
        "calculator": ("app", "calculator"),
        "paint": ("app", "paint"),
        "file explorer": ("app", "file explorer"),
        "explorer": ("app", "file explorer"),
        "task manager": ("app", "task manager"),
        "vs code": ("app", "vs code"),
        # websites
        "youtube": ("site", "youtube"),
        "google": ("site", "google"),
        "github": ("site", "github"),
        "gmail": ("site", "gmail"),
        "chatgpt": ("site", "chatgpt"),
        "instagram": ("site", "instagram"),
        # folders
        "downloads": ("folder", "downloads"),
        "documents": ("folder", "documents"),
        "desktop": ("folder", "desktop"),
        "pictures": ("folder", "pictures"),
        "music": ("folder", "music"),
        "videos": ("folder", "videos"),
    }

    OPEN_VERB_PATTERN = re.compile(
        r"\b(?:open|start|launch|run|"
        r"cheyyi|cheyyandi|chey|cheyara|"
        r"kholo|khol|karo|kar|"
        r"thera|thura)\b"
    )

    GO_PHRASE_PATTERN = re.compile(
        r"\bki\s+(?:vellandi|vellu|vellu\b)"
        r"|\b(?:jaao|jao|jana)\b"
        r"|\bvellandi\b|\bvellu\b"
    )

    CLOSE_VERB_PATTERN = re.compile(
        r"\b(?:close|quit|exit|kill|"
        r"band(?:h)?\s*karo|close\s*cheyyi)\b"
    )

    NEGATION_PATTERN = re.compile(
        r"\b(?:not|dont|don't|can't|cant|"
        r"never|without|_stop)\b"
    )

    MAX_TRANSLIT_WORDS = 6

    # ==================================================
    # EXTENDED PROMPT
    # (original content + mouse_move in the
    #  intent list + extended vocabulary)
    # ==================================================

    PROMPT_TEMPLATE = """
You are LUNA's multilingual computer-command parser.

Understand the user's meaning regardless of language.

Supported intents:

open_application
open_website
open_folder
close_application
take_screenshot
take_webcam_photo
system_info
system_health
battery_status
get_time
get_date
uptime
wifi_status
wifi_scan
increase_volume
decrease_volume
set_volume
set_brightness
brightness_up
brightness_down
mute
unmute
media_play_pause
media_next
media_previous
media_stop
lock_computer
sleep_computer
restart_computer
shutdown_computer
abort_shutdown
mouse_position
mouse_move
click
double_click
right_click
scroll_up
scroll_down
copy
paste
set_clipboard
read_clipboard
type_text
press_key
set_reminder
show_notification
empty_recycle_bin
minimize_window
maximize_window
show_desktop
close_window
youtube_search
google_search
wait
unknown

Supported application targets:

chrome
notepad
calculator
paint
file explorer
task manager
vs code

Supported website targets:

google
youtube
github
gmail
chatgpt
instagram

Supported folder targets:

downloads
documents
desktop
pictures
music
videos

Important:
- Understand Telugu, Hindi, Tamil, Kannada, Malayalam,
  Bengali, Marathi, Gujarati, Punjabi, Urdu, Arabic,
  English and mixed-language speech.
- Understand transliterated speech such as:
  "Chrome open cheyyi"
  "Chrome open karo"
  "YouTube ki vellandi"
- Understand code-switching and mixed-language sentences.
- Extract the actual intent and target.
- Use ONLY the intent names listed above.
- If the message is not a computer command, use "unknown".
- Do not translate the command for the user.
- Return ONLY valid JSON.
- Do not use markdown.
- Do not add explanations.

JSON format:

{{
    "intent": "open_application",
    "target": "chrome",
    "text": null,
    "key": null,
    "x": null,
    "y": null,
    "confidence": 0.98
}}

For type_text, put the text to type in "text".
For youtube_search / google_search, put the search
query in "text".
For set_volume / set_brightness, put the percent
number in "text".
For set_reminder, put the reminder message in "text".
For mouse_move, put numbers in "x" and "y".

User message:

{text}
"""

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

        self.llm_retries = 1

        self._cache = {}

        self._CACHE_LIMIT = 256

        self._stats = {
            "parses": 0,
            "llm_calls": 0,
            "llm_failures": 0,
            "translit_hits": 0,
            "local_fallbacks": 0,
            "json_repairs": 0,
            "rejected_intents": 0,
            "cache_hits": 0,
        }

    # ==================================================
    # RESULT HELPERS
    # ==================================================

    @staticmethod
    def _empty_result():

        return {
            "intent": "unknown",
            "target": None,
            "text": None,
            "key": None,
            "x": None,
            "y": None,
            "confidence": 0.0,
        }

    # ==================================================
    # TRANSLITERATION FAST PATH
    # ==================================================

    def _translit_parse(
        self,
        text,
    ):

        normalized = " ".join(
            str(text or "").lower().split()
        )

        if not normalized:

            return None

        words = normalized.split()

        if (
            len(words)
            > self.MAX_TRANSLIT_WORDS
        ):

            return None

        if self.NEGATION_PATTERN.search(
            normalized
        ):

            return None

        # ------------------------------------------
        # Find the target (longest alias first)
        # ------------------------------------------

        target = None

        kind = None

        for alias in sorted(
            self.TARGET_MAP,
            key=len,
            reverse=True,
        ):

            if re.search(
                r"(?<![a-z])"
                + re.escape(alias)
                + r"(?![a-z])",
                normalized,
            ):

                kind, target = (
                    self.TARGET_MAP[alias]
                )

                break

        if target is None:

            return None

        # ------------------------------------------
        # Close commands
        # ------------------------------------------

        if (
            kind == "app"
            and self.CLOSE_VERB_PATTERN.search(
                normalized
            )
        ):

            self._stats[
                "translit_hits"
            ] += 1

            return {
                "intent": "close_application",
                "target": target,
                "text": None,
                "key": None,
                "x": None,
                "y": None,
                "confidence": 0.80,
            }

        # ------------------------------------------
        # Open commands — verb OR "X ki vellandi"
        # ------------------------------------------

        has_open_verb = (
            self.OPEN_VERB_PATTERN.search(
                normalized
            )
            is not None
        )

        has_go_phrase = (
            self.GO_PHRASE_PATTERN.search(
                normalized
            )
            is not None
        )

        if not (
            has_open_verb or has_go_phrase
        ):

            return None

        if kind == "site":

            intent = "open_website"

        elif kind == "folder":

            intent = "open_folder"

        else:

            intent = "open_application"

        self._stats[
            "translit_hits"
        ] += 1

        return {
            "intent": intent,
            "target": target,
            "text": None,
            "key": None,
            "x": None,
            "y": None,
            "confidence": 0.80,
        }

    # ==================================================
    # PARSE (extended)
    # ==================================================

    def parse(
        self,
        text: str,
    ) -> dict:

        cleaned = str(
            text or ""
        ).strip()

        # FIX: empty text no longer
        # triggers an LLM call.

        if not cleaned:

            return (
                self._empty_result()
            )

        self._stats["parses"] += 1

        cache_key = " ".join(
            cleaned.lower().split()
        )

        cached = self._cache.get(
            cache_key
        )

        if cached is not None:

            self._stats[
                "cache_hits"
            ] += 1

            return dict(cached)

        result = None

        # ==============================================
        # 1) TRANSLITERATION FAST PATH
        # ==============================================

        try:

            result = (
                self._translit_parse(
                    cleaned
                )
            )

        except Exception:

            result = None

        # ==============================================
        # 2) LLM — extended prompt + retry
        # ==============================================

        if result is None:

            prompt = (
                self.PROMPT_TEMPLATE
                .replace(
                    "{text}",
                    cleaned,
                )
            )

            for attempt in range(
                self.llm_retries + 1
            ):

                try:

                    self._stats[
                        "llm_calls"
                    ] += 1

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
                                        "You are a strict "
                                        "JSON computer-command "
                                        "parser. Use only the "
                                        "listed intent names."
                                    )
                                },
                                {
                                    "role": "user",
                                    "content": prompt,
                                }
                            ],
                            temperature=0,
                            max_tokens=250,
                        )
                    )

                    raw = (
                        response
                        .choices[0]
                        .message
                        .content
                        .strip()
                    )

                    data = (
                        self._extract_json(
                            raw
                        )
                    )

                    candidate = (
                        self._validate(
                            data
                        )
                    )

                    if candidate.get(
                        "intent"
                    ) != "unknown":

                        result = candidate

                        break

                    if (
                        attempt
                        < self.llm_retries
                    ):

                        time.sleep(0.4)

                except Exception as error:

                    self._stats[
                        "llm_failures"
                    ] += 1

                    print(
                        f"[NLP] Semantic parser "
                        f"error: {error}"
                    )

                    if (
                        attempt
                        < self.llm_retries
                    ):

                        time.sleep(0.4)

        # ==============================================
        # 3) LOCAL FALLBACK — LLM unreachable
        # ==============================================

        if result is None:

            fallback = (
                self._local_fallback(
                    cleaned
                )
            )

            if fallback is not None:

                self._stats[
                    "local_fallbacks"
                ] += 1

                result = fallback

        if result is None:

            result = (
                self._empty_result()
            )

        # ==============================================
        # CACHE
        # ==============================================

        if (
            len(self._cache)
            >= self._CACHE_LIMIT
        ):

            self._cache.clear()

        self._cache[cache_key] = dict(
            result
        )

        return result

    def _local_fallback(
        self,
        text,
    ):

        try:

            from nlp.intent_classifier import (
                IntentClassifier,
            )

            from nlp.entity_extractor import (
                EntityExtractor,
            )

        except ImportError:

            return None

        try:

            intent = (
                IntentClassifier.classify(
                    text
                )
            )

        except Exception:

            return None

        if intent == "unknown":

            return None

        target = None

        typed_text = None

        key = None

        try:

            if intent in (
                "open_application",
                "close_application",
            ):

                target = (
                    EntityExtractor
                    .find_application(
                        text
                    )
                )

            elif intent == "open_website":

                target = (
                    EntityExtractor
                    .find_website(
                        text
                    )
                )

            elif intent == "open_folder":

                target = (
                    EntityExtractor
                    .find_folder(
                        text
                    )
                )

            elif intent == "type_text":

                typed_text = (
                    EntityExtractor
                    .find_typed_text(
                        text
                    )
                )

            elif intent == "press_key":

                key = (
                    EntityExtractor.find_key(
                        text
                    )
                )

        except Exception:

            pass

        if intent in (
            "open_application",
            "open_website",
            "open_folder",
            "close_application",
        ) and not target:

            return None

        if (
            intent == "type_text"
            and not typed_text
        ):

            return None

        if (
            intent == "press_key"
            and not key
        ):

            return None

        return {
            "intent": intent,
            "target": target,
            "text": typed_text,
            "key": key,
            "x": None,
            "y": None,
            "confidence": 0.65,
        }

    # ==================================================
    # FIX: JSON EXTRACTION (fences + repair)
    # ==================================================

    def _extract_json(
        self,
        raw: str,
    ) -> dict:

        if not raw:

            return {}

        cleaned = str(raw).strip()

        fence = re.search(
            r"```(?:json)?\s*(.*?)\s*```",
            cleaned,
            re.DOTALL,
        )

        if fence:

            cleaned = (
                fence.group(1).strip()
            )

        try:

            return json.loads(
                cleaned
            )

        except json.JSONDecodeError:

            pass

        data = super()._extract_json(
            cleaned
        )

        if data:

            return data

        repaired = (
            self._repair_json(cleaned)
        )

        if repaired is not None:

            self._stats[
                "json_repairs"
            ] += 1

            print(
                "[NLP] Parser JSON repaired."
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
    # FIX: VALIDATION (whitelist + coercion)
    # ==================================================

    def _validate(
        self,
        data,
    ) -> dict:

        base = super()._validate(
            data
        )

        intent = str(
            base.get("intent", "unknown")
        )

        # ------------------------------------------
        # FIX: hallucinated intents rejected
        # ------------------------------------------

        if intent not in (
            self.ALLOWED_INTENTS
        ):

            self._stats[
                "rejected_intents"
            ] += 1

            print(
                f"[NLP] Rejected unknown "
                f"intent from parser: "
                f"{intent!r}"
            )

            return (
                self._empty_result()
            )

        # ------------------------------------------
        # FIX: coerce x / y to int
        # ------------------------------------------

        for name in ("x", "y"):

            value = base.get(name)

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

                    base[name] = None

                    continue

                value = match.group(0)

            try:

                base[name] = int(
                    value
                )

            except (
                TypeError,
                ValueError,
            ):

                base[name] = None

        # ------------------------------------------
        # FIX: clamp confidence to [0, 1]
        # ------------------------------------------

        confidence = base.get(
            "confidence",
            0.0,
        )

        try:

            confidence = float(
                confidence
            )

        except (
            TypeError,
            ValueError,
        ):

            confidence = 0.0

        base["confidence"] = max(
            0.0,
            min(1.0, confidence),
        )

        # ------------------------------------------
        # Normalize target / key / text
        # ------------------------------------------

        target = base.get("target")

        if target is not None:

            base["target"] = (
                str(target).strip().lower()
                or None
            )

        key = base.get("key")

        if key is not None:

            base["key"] = (
                str(key).strip().lower()
                or None
            )

        typed_text = base.get("text")

        if typed_text is not None:

            base["text"] = (
                str(typed_text).strip()
                or None
            )

        return base

    # ==================================================
    # STATS
    # ==================================================

    def get_stats(self):

        return dict(self._stats)


# ------------------------------------------------------------
# DROP-IN UPGRADE
# NLPEngine (and anything else) importing
# MultilingualSemanticParser now gets the extended version
# (same parse() API and result schema).
# Delete the next line to keep the original.
# ------------------------------------------------------------

MultilingualSemanticParser = MultilingualSemanticParserPro


# ============================================================
# QUICK TEST (uncomment to try)
# ============================================================
#
# if __name__ == "__main__":
#
#     parser = MultilingualSemanticParser()
#
#     # 1. Transliteration fast path — instant, no LLM:
#     print(parser.parse("chrome open cheyyi"))
#     print(parser.parse("youtube ki vellandi"))
#     print(parser.parse("notepad kholo"))
#     print(parser.parse("close chrome"))
#
#     # 2. Negation guard — goes to the LLM instead:
#     print(parser.parse("youtube is not opening"))
#
#     # 3. LLM path — multilingual + extended intents:
#     print(parser.parse("బ్యాటరీ లెవెల్ చెప్పు"))
#     print(parser.parse("move the mouse to 500, 400"))
#     print(parser.parse("आवाज़ बंद करो"))
#
#     # 4. Hallucinated intents are rejected:
#     print(parser._validate(
#         {"intent": "order_pizza", "confidence": 0.98}
#     ))
#
#     print(parser.get_stats())