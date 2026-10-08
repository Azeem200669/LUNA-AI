class IntentClassifier:

    @staticmethod
    def classify(
        text: str
    ):

        text = text.lower().strip()

        # ================================================
        # SCREENSHOT
        # ================================================

        if any(
            phrase in text
            for phrase in [
                "screenshot",
                "capture my screen",
                "capture the screen",
                "screen capture",
                "take a picture of the screen",
            ]
        ):

            return "take_screenshot"

        # ================================================
        # SYSTEM INFO
        # ================================================

        if any(
            phrase in text
            for phrase in [
                "system information",
                "system info",
                "computer information",
                "computer specs",
                "pc specs",
                "my computer status",
                "system status",
            ]
        ):

            return "system_info"

        # ================================================
        # VOLUME
        # ================================================

        if any(
            phrase in text
            for phrase in [
                "increase volume",
                "volume up",
                "turn volume up",
                "make it louder",
                "make the sound louder",
                "increase sound",
                "turn the sound up",
            ]
        ):

            return "increase_volume"

        if any(
            phrase in text
            for phrase in [
                "decrease volume",
                "volume down",
                "turn volume down",
                "make it quieter",
                "decrease sound",
                "turn the sound down",
            ]
        ):

            return "decrease_volume"

        # ================================================
        # MUTE
        # ================================================

        if (
            text == "mute"
            or "mute volume" in text
            or "mute my computer" in text
            or "mute the computer" in text
        ):

            return "mute"

        # ================================================
        # UNMUTE
        # ================================================

        if (
            text == "unmute"
            or "unmute volume" in text
            or "unmute my computer" in text
        ):

            return "unmute"

        # ================================================
        # LOCK
        # ================================================

        if any(
            phrase in text
            for phrase in [
                "lock computer",
                "lock my computer",
                "lock the computer",
                "lock my pc",
                "lock the pc",
            ]
        ):

            return "lock_computer"

        # ================================================
        # MOUSE
        # ================================================

        if (
            "where is my mouse" in text
            or "mouse position" in text
            or "mouse location" in text
        ):

            return "mouse_position"

        if (
            text in [
                "click",
                "click here",
                "left click",
            ]
        ):

            return "click"

        if (
            text in [
                "double click",
                "double-click",
            ]
        ):

            return "double_click"

        if (
            text in [
                "right click",
                "right-click",
            ]
        ):

            return "right_click"

        # ================================================
        # SCROLL
        # ================================================

        if (
            "scroll down" in text
            or "scroll downward" in text
        ):

            return "scroll_down"

        if (
            "scroll up" in text
            or "scroll upward" in text
        ):

            return "scroll_up"

        # ================================================
        # COPY / PASTE
        # ================================================

        if text in [
            "copy",
            "copy this",
            "copy that",
        ]:

            return "copy"

        if text in [
            "paste",
            "paste this",
            "paste that",
        ]:

            return "paste"

        # ================================================
        # OPEN APPLICATION
        # ================================================

        application_words = [
            "open",
            "launch",
            "start",
            "run",
            "load",
        ]

        if any(
            word in text
            for word in application_words
        ):

            return "open_application"

        # ================================================
        # OPEN WEBSITE
        # ================================================

        if (
            "go to" in text
            or "visit" in text
            or "open" in text
            or "launch" in text
        ):

            return "open_website"

        # ================================================
        # OPEN FOLDER
        # ================================================

        if (
            "downloads" in text
            or "documents" in text
            or "desktop" in text
            or "pictures" in text
            or "music" in text
            or "videos" in text
        ):

            return "open_folder"

        # ================================================
        # TYPE
        # ================================================

        if (
            text.startswith("type ")
            or text.startswith("write ")
            or text.startswith("enter ")
        ):

            return "type_text"

        # ================================================
        # PRESS KEY
        # ================================================

        if (
            text.startswith("press ")
            or text.startswith("hit ")
        ):

            return "press_key"

        return "unknown"


# ============================================================
# ============================================================
#
#   🌙 LUNA INTENT CLASSIFIER PRO — EXTENSIONS (APPEND ONLY)
#
#   The original IntentClassifier above is 100% unchanged.
#   Pro reimplements classify() with FIXED PRIORITY and
#   word-boundary matching, keeping every original intent
#   name identical so existing planners keep working.
#
#   FIXES
#     • "unmute volume" / "unmute my computer" classified
#       as MUTE — the mute branch ran first and its substring
#       checks match INSIDE the word "unmute" ("un" + "mute
#       volume"). Pro checks unmute first and uses
#       word-boundary \bmute\b.
#     • Substring verb matching — "download" contains "load",
#       "running" contains "run", "started" contains "start",
#       so "latest download news" opened an application.
#       Pro uses \bopen\b / \bload\b boundaries.
#     • Priority order — "open youtube" hit OPEN_APPLICATION
#       (any "open" won) before the website branch was ever
#       reached; "go to documents" hit OPEN_WEBSITE before
#       the folder branch. Pro: folder → website/app entities
#       → generic verbs.
#     • "open google chrome" → website "google" — the app
#       phrase contains the website alias. Pro checks app
#       entities before website entities.
#     • "go to sleep" → open_website (the "go to" branch
#       fired). Pro's power checks run before "go to".
#     • Open-folder branch was nearly unreachable — it sat
#       AFTER two branches that match the same words.
#     • "copyright" matched copy (substring) — word
#       boundary fixes it.
#     • Websites searched instead of opened — "search cats
#       on youtube" / "google weather" now return
#       youtube_search / google_search.
#
#   ADDITIONS
#     • 25+ new intents matching the extended
#       ActionExecutor: battery, system health, wi-fi
#       (status/scan), time, date, uptime, set_volume,
#       set_brightness, brightness up/down, media controls,
#       sleep/restart/shutdown/abort, webcam, clipboard,
#       reminders, notifications, recycle bin, window
#       management, close_application, chat utilities, stop.
#
# ============================================================
# ============================================================

import re


class IntentClassifierPro(IntentClassifier):

    # ==================================================
    # ENTITY TABLES (compact, self-contained)
    # ==================================================

    APP_ALIASES = {
        "google chrome": "chrome",
        "chrome": "chrome",
        "my browser": "chrome",
        "browser": "chrome",

        "notepad": "notepad",
        "calculator": "calculator",
        "paint": "paint",

        "file explorer": "file explorer",
        "explorer": "file explorer",

        "task manager": "task manager",

        "vs code": "vs code",
        "visual studio code": "vs code",

        "spotify": "spotify",
        "discord": "discord",
        "whatsapp": "whatsapp",
        "vlc": "vlc",

        "microsoft word": "word",
        "word": "word",
        "microsoft excel": "excel",
        "excel": "excel",
        "powerpoint": "powerpoint",

        "settings": "settings",
        "camera": "camera",

        "command prompt": "cmd",
        "cmd": "cmd",
        "terminal": "cmd",
        "powershell": "powershell",

        "microsoft edge": "edge",
        "edge": "edge",
        "firefox": "firefox",
    }

    WEBSITE_ALIASES = {
        "youtube": "youtube",
        "google": "google",
        "github": "github",
        "gmail": "gmail",
        "chatgpt": "chatgpt",
        "chat gpt": "chatgpt",
        "instagram": "instagram",
        "facebook": "facebook",
        "twitter": "twitter",
        "netflix": "netflix",
        "amazon": "amazon",
        "reddit": "reddit",
        "linkedin": "linkedin",
        "wikipedia": "wikipedia",
    }

    FOLDER_WORDS = [
        "downloads",
        "documents",
        "desktop",
        "pictures",
        "photos",
        "music",
        "videos",
    ]

    DOMAIN_PATTERN = re.compile(
        r"\b[a-z0-9-]+\."
        r"(?:com|org|net|io|in|co|dev|ai|gov|edu)\b"
    )

    # ==================================================
    # HELPERS
    # ==================================================

    @staticmethod
    def _has(text, pattern):

        return (
            re.search(pattern, text)
            is not None
        )

    @classmethod
    def _find_app(cls, text):

        # longest alias first so "google
        # chrome" wins over "chrome"

        for alias in sorted(
            cls.APP_ALIASES,
            key=len,
            reverse=True,
        ):

            if cls._has(
                text,
                r"(?<![a-z])"
                + re.escape(alias)
                + r"(?![a-z])",
            ):

                return cls.APP_ALIASES[
                    alias
                ]

        return None

    @classmethod
    def _find_website(cls, text):

        for alias in sorted(
            cls.WEBSITE_ALIASES,
            key=len,
            reverse=True,
        ):

            if cls._has(
                text,
                r"(?<![a-z])"
                + re.escape(alias)
                + r"(?![a-z])",
            ):

                return (
                    cls.WEBSITE_ALIASES[
                        alias
                    ]
                )

        if cls._has(
            text,
            cls.DOMAIN_PATTERN,
        ):

            return "domain"

        return None

    @classmethod
    def _has_folder(cls, text):

        for word in cls.FOLDER_WORDS:

            if cls._has(
                text,
                r"(?<![a-z])"
                + word
                + r"(?![a-z])",
            ):

                return True

        return cls._has(
            text,
            r"\bfolders?\b",
        )

    # ==================================================
    # CLASSIFY (fixed priority, word boundaries)
    # ==================================================

    @staticmethod
    def classify(text: str):

        t = " ".join(
            str(text or "").lower().split()
        )

        if not t:

            return "unknown"

        S = IntentClassifierPro

        S._STATS["requests"] += 1

        # ==============================================
        # STOP / CHAT UTILITIES
        # ==============================================

        if t in {
            "stop",
            "stop luna",
            "cancel",
            "cancel luna",
            "stop speaking",
        }:

            return "stop"

        if S._has(
            t,
            r"clear (the |my )?"
            r"(conversation|chat|messages?)",
        ):

            return "clear_chat"

        if S._has(
            t,
            r"(export|save) (the |my )?"
            r"(conversation|chat)",
        ):

            return "export_chat"

        if S._has(
            t,
            r"copy (the |my )?"
            r"(conversation|chat)",
        ):

            return "copy_chat"

        if S._has(t, r"\bstats\b"):

            return "show_stats"

        if t in {
            "help",
            "what can you do",
            "commands",
        }:

            return "help"

        if t in {
            "start demo",
            "demo mode",
            "demo",
        }:

            return "demo"

        if t in {"stop demo"}:

            return "stop_demo"

        # ==============================================
        # MUTE / UNMUTE  (FIX: unmute FIRST,
        # word boundaries so "unmute volume"
        # no longer matches "mute volume")
        # ==============================================

        if S._has(t, r"\bunmute\b"):

            return "unmute"

        if S._has(t, r"\bmute\b"):

            return "mute"

        # ==============================================
        # SCREENSHOT / WEBCAM
        # ==============================================

        if S._has(
            t,
            r"\bscreenshots?\b"
            r"|capture (my |the )?screen"
            r"|screen ?capture"
            r"|picture of (my |the )?screen",
        ):

            return "take_screenshot"

        if S._has(
            t,
            r"\bwebcam\b|\bselfie\b"
            r"|take (a |my )?photo",
        ):

            return "take_webcam_photo"

        # ==============================================
        # SYSTEM
        # ==============================================

        if S._has(
            t,
            r"system (information|info)"
            r"|computer (information|specs)"
            r"|pc specs"
            r"|(my )?computer status"
            r"|system status",
        ):

            return "system_info"

        if S._has(
            t,
            r"\bcpu\b|\bram\b"
            r"|\bmemory usage|\bdisk\b"
            r"|\bstorage\b|\bperformance\b"
            r"|system health",
        ):

            return "system_health"

        if S._has(t, r"\bbattery\b"):

            return "battery_status"

        if S._has(
            t,
            r"\buptime\b"
            r"|how long has (my |the )?"
            r"(computer|pc|laptop|system) been",
        ):

            return "uptime"

        # ==============================================
        # WI-FI
        # ==============================================

        if S._has(t, r"\bwi-?fi\b"):

            if S._has(
                t,
                r"\bscan\b"
                r"|(list|nearby) networks?"
                r"|networks? (list|nearby)",
            ):

                return "wifi_scan"

            return "wifi_status"

        # ==============================================
        # TIME / DATE / UPTIME
        # ==============================================

        if S._has(
            t,
            r"(what|current|tell me)"
            r".{0,12}\btime\b",
        ):

            return "get_time"

        if S._has(
            t,
            r"(what|current|tell me)"
            r".{0,12}\bdate\b"
            r"|what day is it"
            r"|today'?s date"
            r"|date today",
        ):

            return "get_date"

        # ==============================================
        # VOLUME  (exact percent → set_volume)
        # ==============================================

        if re.search(
            r"set (the )?volume "
            r"(?:to|at) (\d{1,3})",
            t,
        ):

            return "set_volume"

        if S._has(
            t,
            r"volume up"
            r"|turn (the )?(volume|sound) up"
            r"|increase (the )?(volume|sound)"
            r"|\blouder\b",
        ):

            return "increase_volume"

        if S._has(
            t,
            r"volume down"
            r"|turn (the )?(volume|sound) down"
            r"|decrease (the )?(volume|sound)"
            r"|\bquieter\b",
        ):

            return "decrease_volume"

        # ==============================================
        # BRIGHTNESS
        # ==============================================

        if re.search(
            r"set (the )?brightness "
            r"(?:to|at) (\d{1,3})",
            t,
        ):

            return "set_brightness"

        if S._has(
            t,
            r"brightness up"
            r"|increase (the )?brightness"
            r"|\bbrighter\b",
        ):

            return "brightness_up"

        if S._has(
            t,
            r"brightness down"
            r"|decrease (the )?brightness"
            r"|\b(dim|dimmer|darker)\b",
        ):

            return "brightness_down"

        # ==============================================
        # MEDIA  (play/search on youtube first)
        # ==============================================

        if S._has(t, r"\byoutube\b|\byt\b") and S._has(
            t,
            r"\bplay\b|\bsearch\b|\bfind\b",
        ):

            return "youtube_search"

        if S._has(t, r"\bgoogle\b") and S._has(
            t,
            r"\bsearch\b|\bfind\b",
        ):

            return "google_search"

        if S._has(
            t,
            r"\bnext (song|track|video)\b|\bskip\b",
        ):

            return "media_next"

        if S._has(
            t,
            r"\bprevious (song|track|video)\b"
            r"|\blast song\b",
        ):

            return "media_previous"

        if S._has(
            t,
            r"\bpause\b|\bresume\b"
            r"|play (some )?music"
            r"|play (a )?song",
        ):

            return "media_play_pause"

        # ==============================================
        # POWER  (FIX: before "go to"/"visit" —
        # "go to sleep" is no longer open_website)
        # ==============================================

        if S._has(
            t,
            r"(abort|cancel) (the )?"
            r"(shutdown|shut down|restart)",
        ):

            return "abort_shutdown"

        if S._has(
            t,
            r"\bshut ?down\b"
            r"|turn off (the |my )?"
            r"(computer|pc|laptop)",
        ):

            return "shutdown_computer"

        if S._has(t, r"\brestart\b|\breboot\b"):

            return "restart_computer"

        if S._has(
            t,
            r"\bsleep\b|\bhibernate\b"
            r"|take a nap",
        ):

            return "sleep_computer"

        if S._has(t, r"\block\b"):

            return "lock_computer"

        # ==============================================
        # SCROLL
        # ==============================================

        if S._has(t, r"scroll (down|downward)"):

            return "scroll_down"

        if S._has(t, r"scroll (up|upward)"):

            return "scroll_up"

        # ==============================================
        # MOUSE / CLICKS
        # (FIX: double/right checked before click)
        # ==============================================

        if S._has(
            t,
            r"where is my mouse"
            r"|mouse (position|location)",
        ):

            return "mouse_position"

        if S._has(t, r"\bdouble[- ]?click\b"):

            return "double_click"

        if S._has(t, r"\bright[- ]?click\b"):

            return "right_click"

        if S._has(t, r"\bclick\b"):

            return "click"

        # ==============================================
        # CLIPBOARD / COPY / PASTE
        # (FIX: \bcopy\b no longer matches
        #  "copyright"; clipboard phrases first)
        # ==============================================

        if S._has(t, r"\bclipboard\b"):

            if S._has(t, r"\bcopy\b"):

                return "set_clipboard"

            return "read_clipboard"

        if S._has(t, r"\bcopy\b"):

            return "copy"

        if S._has(t, r"\bpaste\b"):

            return "paste"

        # ==============================================
        # FOLDER  (FIX: checked BEFORE app/website
        # so "open downloads" and "go to documents"
        # are open_folder)
        # ==============================================

        folder_hit = S._has_folder(t)

        if folder_hit and S._has(
            t,
            r"\b(open|go to|show|launch|visit)\b",
        ):

            return "open_folder"

        if (
            folder_hit
            and len(t.split()) <= 3
        ):

            return "open_folder"

        # ==============================================
        # ENTITIES: app BEFORE website
        # (FIX: "open google chrome" → application)
        # ==============================================

        app_entity = S._find_app(t)

        website_entity = S._find_website(t)

        if S._has(t, r"\b(close|quit|kill)\b") and app_entity:

            return "close_application"

        if app_entity and S._has(
            t,
            r"\b(open|launch|start|run|load)\b",
        ):

            return "open_application"

        if website_entity and S._has(
            t,
            r"\b(open|go to|visit|launch|show)\b",
        ):

            return "open_website"

        if website_entity:

            return "open_website"

        # ==============================================
        # TYPE / PRESS
        # ==============================================

        if t.startswith(
            ("type ", "write ", "enter ")
        ):

            return "type_text"

        if t.startswith(("press ", "hit ")):

            return "press_key"

        # ==============================================
        # REMINDER / NOTIFICATION / EXTRAS
        # ==============================================

        if S._has(t, r"remind me"):

            return "set_reminder"

        if S._has(
            t,
            r"send (me )?(a )?notification"
            r"|notify me",
        ):

            return "show_notification"

        if S._has(
            t,
            r"(empty|clear) (the )?recycle bin",
        ):

            return "empty_recycle_bin"

        if S._has(t, r"show (the )?desktop"):

            return "show_desktop"

        if S._has(t, r"\bminimi[sz]e\b"):

            return "minimize_window"

        if S._has(t, r"\bmaximi[sz]e\b"):

            return "maximize_window"

        if S._has(t, r"close (the |this )?window"):

            return "close_window"

        # ==============================================
        # GENERIC VERB FALLBACKS
        # (same as base, but word-boundary —
        #  "download" no longer triggers "load")
        # ==============================================

        if S._has(
            t,
            r"\b(open|launch|start|run|load)\b",
        ):

            return "open_application"

        if S._has(t, r"\bgo to\b|\bvisit\b"):

            return "open_website"

        S._STATS["unknown"] += 1

        return "unknown"

    # ==================================================
    # STATS + REGISTRY
    # ==================================================

    _STATS = {
        "requests": 0,
        "unknown": 0,
    }

    @classmethod
    def get_stats(cls):

        stats = dict(cls._STATS)

        if stats["requests"]:

            stats["unknown_rate"] = round(
                stats["unknown"]
                / stats["requests"],
                3,
            )

        return stats

    @classmethod
    def known_intents(cls):

        return [
            # original
            "take_screenshot", "system_info",
            "increase_volume", "decrease_volume",
            "mute", "unmute", "lock_computer",
            "mouse_position", "click", "double_click",
            "right_click", "scroll_up", "scroll_down",
            "copy", "paste", "open_application",
            "open_website", "open_folder",
            "type_text", "press_key", "unknown",
            # new
            "stop", "clear_chat", "export_chat",
            "copy_chat", "show_stats", "help",
            "demo", "stop_demo", "take_webcam_photo",
            "system_health", "battery_status",
            "uptime", "wifi_status", "wifi_scan",
            "get_time", "get_date", "set_volume",
            "set_brightness", "brightness_up",
            "brightness_down", "youtube_search",
            "google_search", "media_next",
            "media_previous", "media_play_pause",
            "abort_shutdown", "shutdown_computer",
            "restart_computer", "sleep_computer",
            "set_clipboard", "read_clipboard",
            "close_application", "set_reminder",
            "show_notification", "empty_recycle_bin",
            "show_desktop", "minimize_window",
            "maximize_window", "close_window",
        ]


# ------------------------------------------------------------
# DROP-IN UPGRADE
# Anything importing IntentClassifier now gets the extended
# version (static call style IntentClassifier.classify(text)
# still works). Delete the next line to keep the original.
# ------------------------------------------------------------

IntentClassifier = IntentClassifierPro


# ============================================================
# QUICK TEST (uncomment to try)
# ============================================================
#
# if __name__ == "__main__":
#
#     tests = [
#         # FIXED behaviors:
#         ("unmute volume",           "unmute"),         # was "mute"
#         ("unmute my computer",      "unmute"),         # was "mute"
#         ("latest download news",    "unknown"),        # was open_application
#         ("the server is running",   "unknown"),        # was open_application
#         ("open youtube",            "open_website"),   # was open_application
#         ("go to documents",         "open_folder"),    # was open_website
#         ("open downloads",          "open_folder"),    # was open_application
#         ("open google chrome",      "open_application"),
#         ("go to sleep",             "sleep_computer"), # was open_website
#         ("copyright law",           "unknown"),        # was "copy"
#         ("cancel the shutdown",     "abort_shutdown"),
#         # NEW abilities:
#         ("what's my battery level", "battery_status"),
#         ("set volume to 40",        "set_volume"),
#         ("play lofi on youtube",    "youtube_search"),
#         ("next song",               "media_next"),
#         ("remind me in 10 minutes", "set_reminder"),
#         ("read my clipboard",       "read_clipboard"),
#     ]
#
#     for text, expected in tests:
#         result = IntentClassifier.classify(text)
#         mark = "✅" if result == expected else "❌"
#         print(f"{mark} '{text}' → {result}")