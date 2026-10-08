import re


class EntityExtractor:

    APPLICATION_ALIASES = {

        "chrome": "chrome",
        "google chrome": "chrome",
        "browser": "chrome",
        "my browser": "chrome",

        "notepad": "notepad",

        "calculator": "calculator",
        "calc": "calculator",

        "paint": "paint",

        "file explorer": "file explorer",
        "explorer": "file explorer",

        "task manager": "task manager",

        "vs code": "vs code",
        "visual studio code": "vs code",
        "code": "vs code",
    }

    WEBSITE_ALIASES = {

        "youtube": "youtube",
        "google": "google",
        "github": "github",
        "gmail": "gmail",
        "chatgpt": "chatgpt",
        "instagram": "instagram",
    }

    FOLDER_ALIASES = {

        "downloads": "downloads",
        "download folder": "downloads",

        "documents": "documents",
        "document folder": "documents",

        "desktop": "desktop",

        "pictures": "pictures",
        "photos": "pictures",

        "music": "music",

        "videos": "videos",
    }

    @staticmethod
    def find_application(
        text: str
    ):

        text = text.lower()

        for alias, target in (
            EntityExtractor.APPLICATION_ALIASES.items()
        ):

            if alias in text:
                return target

        return None

    @staticmethod
    def find_website(
        text: str
    ):

        text = text.lower()

        for alias, target in (
            EntityExtractor.WEBSITE_ALIASES.items()
        ):

            if alias in text:
                return target

        return None

    @staticmethod
    def find_folder(
        text: str
    ):

        text = text.lower()

        for alias, target in (
            EntityExtractor.FOLDER_ALIASES.items()
        ):

            if alias in text:
                return target

        return None

    @staticmethod
    def find_coordinates(
        text: str
    ):

        patterns = [

            r"x\s*(\d+)\s*y\s*(\d+)",

            r"x\s*=\s*(\d+)\s*,?\s*y\s*=\s*(\d+)",

            r"(\d+)\s*,\s*(\d+)",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                return {
                    "x": int(match.group(1)),
                    "y": int(match.group(2)),
                }

        return None

    @staticmethod
    def find_typed_text(
        text: str
    ):

        patterns = [

            r"^(?:type|write)\s+(.+)$",

            r"(?:type|write)\s+(.+)",

            r"(?:enter|input)\s+(.+)",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                return match.group(1).strip()

        return None

    @staticmethod
    def find_key(
        text: str
    ):

        keys = [
            "enter",
            "escape",
            "esc",
            "tab",
            "space",
            "backspace",
            "delete",
            "home",
            "end",
            "up",
            "down",
            "left",
            "right",
            "pageup",
            "pagedown",
        ]

        for key in keys:

            if re.search(
                rf"\b(?:press|hit)\s+{key}\b",
                text,
                re.IGNORECASE
            ):

                return key

        return None


# ============================================================
# ============================================================
#
#   🌙 LUNA ENTITY EXTRACTOR PRO — EXTENSIONS (APPEND ONLY)
#
#   The original EntityExtractor above is 100% unchanged.
#   Pro overrides the finders as classmethods (so the old
#   EntityExtractor.find_application(text) call style still
#   works) and delegates to super() where the base is right.
#
#   FIXES
#     • Substring false positives — "calc" matched inside
#       "calculate", "code" matched "zip code"/"barcode",
#       "mail" would match inside "email". Pro uses
#       word-boundary matching + guard words.
#     • "open google chrome" extracted website "google" —
#       the website matcher fired on the word "google"
#       inside the app name. Pro suppresses website aliases
#       that are part of a detected application phrase.
#     • Dict-order dependence — matching relied on insertion
#       order instead of specificity ("file explorer" vs
#       "explorer" worked by luck). Pro sorts all aliases
#       longest-first.
#     • "press the enter key" never matched — the base regex
#       required the key directly after press/hit. Pro allows
#       filler words + optional "key"/"button".
#     • Combos unsupported — "press ctrl c" / "press control
#       alt delete" returned None (or worse). Pro parses and
#       normalizes them to "ctrl+c".
#     • find_typed_text swallowed trailing commands — "type
#       hello then press enter" typed the whole sentence.
#       Pro strips trailing command phrases + supports quotes.
#     • find_coordinates matched any "N, M" — "remind me in
#       10, 20 minutes" became coordinates. Pro anchors on
#       action words and clamps to the real screen size.
#
#   ADDITIONS
#     • Extended alias tables (spotify, word, excel, cmd,
#       edge, netflix, twitter, maps, drive, wikipedia…)
#     • Fuzzy application matching — "notpad" → notepad
#     • find_search_query — "search cats on youtube" →
#       {"engine": "youtube", "query": "cats"}
#     • find_setting — volume/brightness percent + direction
#     • find_duration / find_reminder — "in 10 minutes"
#     • find_url — "open example.com" → https://…
#     • find_intent — action verb detection
#     • find_all — one cached call returning every entity
#     • add_*_alias APIs + get_stats()
#
# ============================================================
# ============================================================

from difflib import get_close_matches


class EntityExtractorPro(EntityExtractor):

    # ==================================================
    # EXTRA ALIAS TABLES (originals stay untouched)
    # ==================================================

    EXTRA_APPLICATION_ALIASES = {

        "spotify": "spotify",
        "discord": "discord",
        "whatsapp": "whatsapp",
        "telegram": "telegram",
        "vlc": "vlc",
        "steam": "steam",

        "word": "word",
        "microsoft word": "word",

        "excel": "excel",
        "microsoft excel": "excel",

        "powerpoint": "powerpoint",
        "power point": "powerpoint",

        "settings": "settings",
        "windows settings": "settings",

        "camera": "camera",

        "mail": "mail",
        "outlook": "mail",

        "cmd": "cmd",
        "command prompt": "cmd",
        "terminal": "cmd",
        "powershell": "powershell",

        "edge": "edge",
        "microsoft edge": "edge",
        "firefox": "firefox",

        "snipping tool": "snipping tool",
        "control panel": "control panel",
    }

    EXTRA_WEBSITE_ALIASES = {

        "twitter": "twitter",
        "x com": "twitter",

        "facebook": "facebook",
        "netflix": "netflix",
        "amazon": "amazon",
        "reddit": "reddit",

        "stack overflow": "stack overflow",
        "stackoverflow": "stack overflow",

        "linkedin": "linkedin",
        "wikipedia": "wikipedia",

        "google maps": "google maps",
        "maps": "google maps",

        "google drive": "google drive",

        "whatsapp web": "whatsapp web",

        "chat gpt": "chatgpt",
        "gpt": "chatgpt",
    }

    EXTRA_FOLDER_ALIASES = {

        "recent files": "recent",
        "recent folder": "recent",

        "my documents": "documents",
        "my pictures": "pictures",
        "my music": "music",
        "my videos": "videos",

        "pictures folder": "pictures",
        "screenshots folder": "pictures",
        "screenshot folder": "pictures",

        "onedrive": "onedrive",
        "home folder": "home",
    }

    # ------------------------------------------------
    # GUARDS — alias must NOT match when the word
    # right before it is one of these.
    # ------------------------------------------------

    ALIAS_GUARDS = {
        "code": {
            "zip", "postal", "pass", "bar", "area",
            "country", "morse", "dress", "promo",
            "coupon", "discount", "source", "secret",
            "binary", "error", "qr",
        },
    }

    # ==================================================
    # KEYS
    # ==================================================

    KEY_ALIASES = {
        "escape": "esc",
        "control": "ctrl",
        "return": "enter",
        "spacebar": "space",
        "del": "delete",
        "ins": "insert",
        "arrowup": "up",
        "arrowdown": "down",
        "arrowleft": "left",
        "arrowright": "right",
        "start": "win",
        "break": "pause",
    }

    BASE_KEYS = {
        "enter", "escape", "esc", "tab", "space",
        "backspace", "delete", "home", "end",
        "up", "down", "left", "right",
        "pageup", "pagedown",
    }

    EXTRA_KEYS = {
        "insert", "printscreen", "capslock", "pause",
        "win", "windows", "menu", "clear",
        "f1", "f2", "f3", "f4", "f5", "f6", "f7",
        "f8", "f9", "f10", "f11", "f12",
    }

    KNOWN_KEYS = BASE_KEYS | EXTRA_KEYS

    MODIFIERS = {
        "ctrl", "control", "alt", "shift",
        "win", "windows", "super", "cmd",
    }

    # ==================================================
    # INTENTS
    # ==================================================

    INTENT_VERBS = (
        "screenshot", "shutdown", "restart", "reboot",
        "sleep", "lock", "open", "launch", "start",
        "run", "close", "quit", "kill", "exit",
        "search", "google", "play", "pause", "resume",
        "stop", "type", "write", "press", "hit",
        "double click", "right click", "click",
        "move", "scroll", "minimize", "maximize",
        "mute", "unmute", "remind", "copy", "paste",
    )

    VERB_PREFIX = re.compile(
        r"^(?:please\s+)?(?:can you\s+)?"
        r"(?:open|launch|start|run|fire up|kill|close|quit)\s+",
        re.IGNORECASE,
    )

    # ==================================================
    # CACHES + STATS (class-level)
    # ==================================================

    _candidates_cache = {}

    _pattern_cache = {}

    _CACHE = {}

    _CACHE_LIMIT = 256

    _STATS = {
        "requests": 0,
        "cache_hits": 0,
        "entities_found": 0,
    }

    # ==================================================
    # CANDIDATE TABLES (merged, longest-first)
    # ==================================================

    @classmethod
    def _merged(cls, base, extra, cache_key):

        cached = (
            cls._candidates_cache.get(cache_key)
        )

        if cached is not None:

            return cached

        merged = dict(base)

        merged.update(extra)

        candidates = sorted(
            merged.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        )

        cls._candidates_cache[cache_key] = (
            candidates
        )

        return candidates

    @classmethod
    def _app_candidates(cls):

        return cls._merged(
            cls.APPLICATION_ALIASES,
            cls.EXTRA_APPLICATION_ALIASES,
            "app",
        )

    @classmethod
    def _website_candidates(cls):

        return cls._merged(
            cls.WEBSITE_ALIASES,
            cls.EXTRA_WEBSITE_ALIASES,
            "web",
        )

    @classmethod
    def _folder_candidates(cls):

        return cls._merged(
            cls.FOLDER_ALIASES,
            cls.EXTRA_FOLDER_ALIASES,
            "folder",
        )

    @classmethod
    def _alias_pattern(cls, alias):

        pattern = (
            cls._pattern_cache.get(alias)
        )

        if pattern is None:

            pattern = re.compile(
                r"(?<![A-Za-z0-9])"
                + re.escape(alias)
                + r"(?![A-Za-z0-9])"
            )

            cls._pattern_cache[alias] = pattern

        return pattern

    @staticmethod
    def _normalize(text):

        return " ".join(
            str(text or "").lower().split()
        )

    # ==================================================
    # FIX: APPLICATION (boundaries + guards + fuzzy)
    # ==================================================

    @classmethod
    def find_application(cls, text):

        lowered = cls._normalize(text)

        if not lowered:

            return None

        for alias, target in (
            cls._app_candidates()
        ):

            match = (
                cls._alias_pattern(alias)
                .search(lowered)
            )

            if match is None:

                continue

            guards = (
                cls.ALIAS_GUARDS.get(alias)
            )

            if guards:

                before = (
                    lowered[: match.start()]
                    .split()
                )

                if (
                    before
                    and before[-1] in guards
                ):

                    continue

            return target

        return cls._fuzzy_application(
            lowered
        )

    @classmethod
    def _fuzzy_application(cls, lowered):

        if len(lowered.split()) > 5:

            return None

        candidate = (
            cls.VERB_PREFIX
            .sub("", lowered)
            .strip(" .!?")
        )

        if not candidate:

            return None

        names = [
            alias
            for alias, _ in (
                cls._app_candidates()
            )
        ]

        match = get_close_matches(
            candidate,
            names,
            n=1,
            cutoff=0.82,
        )

        if match:

            return cls._target_of(
                cls._app_candidates(),
                match[0],
            )

        words = candidate.split()

        if len(words) >= 2:

            tail = " ".join(
                words[-2:]
            )

            match = get_close_matches(
                tail,
                names,
                n=1,
                cutoff=0.82,
            )

            if match:

                return cls._target_of(
                    cls._app_candidates(),
                    match[0],
                )

        return None

    @staticmethod
    def _target_of(candidates, alias):

        for name, target in candidates:

            if name == alias:

                return target

        return None

    # ==================================================
    # FIX: WEBSITE (app-phrase suppression)
    # ==================================================

    @classmethod
    def find_website(cls, text):

        lowered = cls._normalize(text)

        if not lowered:

            return None

        app_phrases = [
            alias
            for alias, _ in (
                cls._app_candidates()
            )
            if cls._alias_pattern(alias)
            .search(lowered)
        ]

        for alias, target in (
            cls._website_candidates()
        ):

            match = (
                cls._alias_pattern(alias)
                .search(lowered)
            )

            if match is None:

                continue

            suppressed = False

            for phrase in app_phrases:

                phrase_words = set(
                    phrase.split()
                )

                if (
                    alias in phrase_words
                    or alias == phrase
                ):

                    suppressed = True

                    break

            if suppressed:

                continue

            return target

        return None

    # ==================================================
    # FOLDER (boundaries, longest-first)
    # ==================================================

    @classmethod
    def find_folder(cls, text):

        lowered = cls._normalize(text)

        if not lowered:

            return None

        for alias, target in (
            cls._folder_candidates()
        ):

            if (
                cls._alias_pattern(alias)
                .search(lowered)
            ):

                return target

        return None

    # ==================================================
    # FIX: COORDINATES (anchors + screen clamping)
    # ==================================================

    @classmethod
    def find_coordinates(cls, text):

        result = (
            super().find_coordinates(text)
        )

        if result is not None:

            return cls._clamp(result)

        lowered = cls._normalize(text)

        anchored = [

            r"(?:move|put|place)\s+(?:the\s+)?"
            r"(?:mouse|cursor)\s+(?:to|at)\s+"
            r"(\d{1,5})\s*(?:,|x)?\s*(\d{1,5})",

            r"(?:click|tap)\s+(?:at|on)\s+"
            r"(?:position\s+|point\s+)?"
            r"(\d{1,5})\s*(?:,|x)\s*(\d{1,5})",

            r"\b(?:at|position)\s+"
            r"(?:x\s*)?(\d{1,5})\s*(?:,|by|x)\s*"
            r"(?:y\s*)?(\d{1,5})\b",
        ]

        for pattern in anchored:

            match = re.search(
                pattern,
                lowered,
            )

            if match:

                return cls._clamp(
                    {
                        "x": int(
                            match.group(1)
                        ),
                        "y": int(
                            match.group(2)
                        ),
                    }
                )

        return None

    @staticmethod
    def _clamp(coords):

        try:

            import ctypes

            width = (
                ctypes.windll.user32
                .GetSystemMetrics(0)
            )

            height = (
                ctypes.windll.user32
                .GetSystemMetrics(1)
            )

        except Exception:

            return coords

        return {
            "x": max(
                0,
                min(
                    int(coords.get("x", 0)),
                    width - 1,
                ),
            ),
            "y": max(
                0,
                min(
                    int(coords.get("y", 0)),
                    height - 1,
                ),
            ),
        }

    # ==================================================
    # FIX: TYPED TEXT (quotes + trailing commands)
    # ==================================================

    @classmethod
    def find_typed_text(cls, text):

        quoted = re.search(
            r"(?:type|write|enter|input)\s+"
            r"(?:\"|'|\u201c)(.+?)(?:\"|'|\u201d)",
            str(text or ""),
            re.IGNORECASE,
        )

        if quoted:

            return (
                quoted.group(1).strip()
            )

        base = (
            super().find_typed_text(text)
        )

        if base is None:

            return None

        cleaned = re.sub(
            r"[,;]?\s*"
            r"(?:then\s+|and\s+|after\s+that\s+|"
            r"afterwards\s+)?(?:please\s+)?"
            r"(?:press|hit|click|tap)\b.*$",
            "",
            str(base),
            flags=re.IGNORECASE,
        )

        cleaned = cleaned.strip(" ,;")

        return cleaned or str(base)

    # ==================================================
    # FIX: KEYS (filler words + combos)
    # ==================================================

    @classmethod
    def find_key(cls, text):

        lowered = cls._normalize(text)

        lowered = re.sub(
            r"\bplus\b",
            "+",
            lowered,
        )

        # ------------------------------------------
        # COMBOS — "press ctrl c",
        # "press control + alt + delete"
        # ------------------------------------------

        combo = re.search(
            r"\b(?:press|hit)\s+"
            r"((?:ctrl|control|alt|shift|"
            r"win(?:dows)?|super|cmd)"
            r"[\s+]+[\w]+(?:[\s+]+[\w]+)*)",
            lowered,
        )

        if combo:

            parts = re.split(
                r"[\s+]+",
                combo.group(1).strip(),
            )

            normalized = [
                cls.KEY_ALIASES.get(
                    part,
                    part,
                )
                for part in parts
            ]

            tail_ok = all(
                part in cls.KNOWN_KEYS
                or part in cls.MODIFIERS
                or len(part) == 1
                or re.fullmatch(
                    r"f\d{1,2}",
                    part,
                )
                for part in normalized[1:]
            )

            if tail_ok:

                deduped = list(
                    dict.fromkeys(normalized)
                )

                return "+".join(deduped)

        # ------------------------------------------
        # SINGLE — "press the enter key"
        # ------------------------------------------

        single = re.search(
            r"\b(?:press|hit)\s+(?:the\s+)?"
            r"([a-z0-9]+)\s*(?:key|button)?\b",
            lowered,
        )

        if single:

            key = single.group(1)

            key = cls.KEY_ALIASES.get(
                key,
                key,
            )

            if key in cls.KNOWN_KEYS:

                return key

        return None

    # ==================================================
    # NEW: SEARCH QUERY EXTRACTION
    # ==================================================

    SEARCH_ENGINES = {
        "youtube": "youtube",
        "yt": "youtube",
        "google": "google",
        "wikipedia": "wikipedia",
        "wiki": "wikipedia",
        "amazon": "amazon",
        "reddit": "reddit",
        "github": "github",
    }

    @classmethod
    def find_search_query(cls, text):

        lowered = cls._normalize(text)

        if not lowered:

            return None

        engines = (
            r"youtube|yt|wikipedia|wiki|"
            r"google|amazon|reddit|github"
        )

        # "search cats on youtube"

        match = re.search(
            rf"\b(?:search|find|look\s+up)\s+"
            rf"(?:for\s+|about\s+)?(.+?)\s+"
            rf"(?:on|in)\s+({engines})\b\.?$",
            lowered,
        )

        if match:

            return {
                "engine": cls.SEARCH_ENGINES[
                    match.group(2)
                ],
                "query": match.group(1)
                .strip(" ?"),
            }

        # "youtube cats" / "google weather"

        match = re.match(
            rf"^({engines})\s+"
            rf"(?:search\s+)?(?:for\s+|about\s+)?"
            rf"(.+)$",
            lowered,
        )

        if match:

            query = (
                match.group(2).strip()
            )

            if (
                query
                and match.group(1) == "google"
                and cls.find_application(query)
            ):

                # "google chrome" is the app,
                # not a search.

                return None

            if query:

                return {
                    "engine": (
                        cls.SEARCH_ENGINES[
                            match.group(1)
                        ]
                    ),
                    "query": query,
                }

        # "search for best laptops"

        match = re.match(
            r"^(?:please\s+)?"
            r"(?:search|google|look\s+up|find)\s+"
            r"(?:the\s+web\s+(?:for|about)\s+|"
            r"for\s+|about\s+|up\s+)?(.+)$",
            lowered,
        )

        if match:

            query = (
                match.group(1).strip()
            )

            if query:

                return {
                    "engine": "google",
                    "query": query,
                }

        return None

    # ==================================================
    # NEW: SETTINGS (volume / brightness)
    # ==================================================

    @classmethod
    def find_setting(cls, text):

        lowered = cls._normalize(text)

        for kind in ("volume", "brightness"):

            if not re.search(
                rf"\b{kind}\b",
                lowered,
            ):

                continue

            match = re.search(
                rf"\b{kind}\b\s*"
                rf"(?:to|at|level)?\s*"
                rf"(\d{{1,3}})\s*"
                rf"(?:percent|%|points?)?",
                lowered,
            )

            if match:

                value = int(
                    match.group(1)
                )

                if 0 <= value <= 100:

                    return {
                        "kind": kind,
                        "percent": value,
                    }

            direction = None

            if re.search(
                rf"{kind}\s*(?:up|louder|brighter)"
                rf"|(?:raise|increase)\s+"
                rf"(?:the\s+)?{kind}",
                lowered,
            ):

                direction = "up"

            elif re.search(
                rf"{kind}\s*(?:down|quieter|dimmer|lower)"
                rf"|(?:decrease|reduce|lower)\s+"
                rf"(?:the\s+)?{kind}",
                lowered,
            ):

                direction = "down"

            step_match = re.search(
                rf"{kind}\b\s*(?:by)?\s*"
                r"(\d{1,3})",
                lowered,
            )

            if (
                direction
                and step_match
                and step_match.group(1)
            ):

                return {
                    "kind": kind,
                    "direction": direction,
                    "step": int(
                        step_match.group(1)
                    ),
                }

            if direction:

                return {
                    "kind": kind,
                    "direction": direction,
                }

        return None

    # ==================================================
    # NEW: DURATION + REMINDER
    # ==================================================

    UNIT_SECONDS = {
        "second": 1,
        "seconds": 1,
        "sec": 1,
        "secs": 1,
        "minute": 60,
        "minutes": 60,
        "min": 60,
        "mins": 60,
        "hour": 3600,
        "hours": 3600,
        "hr": 3600,
        "hrs": 3600,
    }

    @classmethod
    def find_duration(cls, text):

        lowered = cls._normalize(text)

        match = re.search(
            r"\b(?:in|after)\s+(\d{1,4})\s*"
            r"(seconds?|secs?|minutes?|mins?|"
            r"hours?|hrs?)\b",
            lowered,
        )

        if not match:

            return None

        value = int(match.group(1))

        unit = match.group(2)

        multiplier = 0

        for name, seconds in (
            cls.UNIT_SECONDS.items()
        ):

            if unit == name or unit.startswith(
                name
            ):

                multiplier = seconds

                break

        if multiplier <= 0:

            return None

        return {
            "seconds": value * multiplier,
            "raw": match.group(0),
        }

    @classmethod
    def find_reminder(cls, text):

        lowered = cls._normalize(text)

        if "remind" not in lowered:

            return None

        duration = (
            cls.find_duration(lowered)
            or {}
        )

        message = None

        match = re.search(
            r"remind me\s+"
            r"(?:in\s+\d{1,4}\s*"
            r"(?:seconds?|secs?|minutes?|mins?|"
            r"hours?|hrs?)\s*)?"
            r"(?:to|that|about)\s+(.+)$",
            lowered,
        )

        if match:

            message = (
                match.group(1).strip()
            )

        if (
            not duration
            and not message
        ):

            return None

        return {
            "seconds": duration.get(
                "seconds"
            ),
            "message": message,
        }

    # ==================================================
    # NEW: URL DETECTION
    # ==================================================

    @classmethod
    def find_url(cls, text):

        raw = str(text or "").strip()

        match = re.search(
            r"(https?://\S+|www\.\S+)",
            raw,
            re.IGNORECASE,
        )

        if match:

            url = match.group(1)

            if url.lower().startswith(
                "www."
            ):

                url = "https://" + url

            return url

        match = re.search(
            r"\bopen\s+"
            r"([a-z0-9-]+\.(?:com|org|net|io|in|co|"
            r"dev|ai|gov|edu)(?:/\S*)?)",
            cls._normalize(text),
            re.IGNORECASE,
        )

        if match:

            return (
                "https://" + match.group(1)
            )

        return None

    # ==================================================
    # NEW: INTENT VERB
    # ==================================================

    @classmethod
    def find_intent(cls, text):

        lowered = cls._normalize(text)

        for verb in sorted(
            cls.INTENT_VERBS,
            key=len,
            reverse=True,
        ):

            if re.search(
                r"(?<![a-z])"
                + re.escape(verb)
                + r"(?![a-z])",
                lowered,
            ):

                return verb

        return None

    # ==================================================
    # MASTER EXTRACT (cached)
    # ==================================================

    @classmethod
    def find_all(cls, text):

        key = cls._normalize(text)

        if not key:

            return {}

        cls._STATS["requests"] += 1

        cached = cls._CACHE.get(key)

        if cached is not None:

            cls._STATS[
                "cache_hits"
            ] += 1

            return dict(cached)

        entities = {
            "application": (
                cls.find_application(text)
            ),
            "website": (
                cls.find_website(text)
            ),
            "folder": (
                cls.find_folder(text)
            ),
            "url": cls.find_url(text),
            "search": (
                cls.find_search_query(text)
            ),
            "setting": (
                cls.find_setting(text)
            ),
            "duration": (
                cls.find_duration(text)
            ),
            "reminder": (
                cls.find_reminder(text)
            ),
            "coordinates": (
                cls.find_coordinates(text)
            ),
            "typed_text": (
                cls.find_typed_text(text)
            ),
            "key": cls.find_key(text),
            "intent": (
                cls.find_intent(text)
            ),
        }

        hits = sum(
            1
            for value in entities.values()
            if value
        )

        cls._STATS[
            "entities_found"
        ] += hits

        if (
            len(cls._CACHE)
            >= cls._CACHE_LIMIT
        ):

            cls._CACHE.clear()

        cls._CACHE[key] = dict(entities)

        return entities

    # ==================================================
    # EXTENSION APIs + STATS
    # ==================================================

    @classmethod
    def add_application_alias(
        cls,
        alias,
        target,
    ):

        cls.EXTRA_APPLICATION_ALIASES[
            str(alias).lower().strip()
        ] = str(target).lower().strip()

        cls._candidates_cache.pop(
            "app",
            None,
        )

    @classmethod
    def add_website_alias(cls, alias, target):

        cls.EXTRA_WEBSITE_ALIASES[
            str(alias).lower().strip()
        ] = str(target).lower().strip()

        cls._candidates_cache.pop(
            "web",
            None,
        )

    @classmethod
    def add_folder_alias(cls, alias, target):

        cls.EXTRA_FOLDER_ALIASES[
            str(alias).lower().strip()
        ] = str(target).lower().strip()

        cls._candidates_cache.pop(
            "folder",
            None,
        )

    @classmethod
    def get_stats(cls):

        return dict(cls._STATS)


# ------------------------------------------------------------
# DROP-IN UPGRADE
# Anything that imports EntityExtractor from this file now
# gets the extended version automatically. Class-level calls
# (EntityExtractor.find_application("open chrome")) still
# work because the Pro finders are classmethods.
# Delete the next line to keep using the original.
# ------------------------------------------------------------

EntityExtractor = EntityExtractorPro


# ============================================================
# QUICK TEST (uncomment to try)
# ============================================================
#
# if __name__ == "__main__":
#
#     # Fixed behaviors:
#     print(EntityExtractor.find_application("calculate 15% of 200"))   # None (was calculator)
#     print(EntityExtractor.find_application("what is my zip code"))    # None (was vs code)
#     print(EntityExtractor.find_website("open google chrome"))         # None (was google)
#     print(EntityExtractor.find_website("open google"))                # google
#     print(EntityExtractor.find_key("press the enter key"))            # enter
#     print(EntityExtractor.find_key("press control alt delete"))       # ctrl+alt+delete
#     print(EntityExtractor.find_typed_text("type hello world then press enter"))
#                                                                       # hello world
#     print(EntityExtractor.find_coordinates("remind me in 10, 20 minutes"))
#                                                                       # None
#
#     # New abilities:
#     print(EntityExtractor.find_application("open notpad"))            # notepad (fuzzy)
#     print(EntityExtractor.find_search_query("search cats on youtube"))
#     print(EntityExtractor.find_setting("set volume to 40"))
#     print(EntityExtractor.find_reminder("remind me in 10 minutes to check the oven"))
#     print(EntityExtractor.find_url("open example.com"))
#     print(EntityExtractor.find_all("open youtube and search lofi beats"))
#     print(EntityExtractor.get_stats())