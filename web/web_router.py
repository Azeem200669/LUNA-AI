import re
from typing import Optional

from web.web_intelligence import WebIntelligence


class WebRouter:

    def __init__(self):

        self.web = WebIntelligence()

    # ========================================================
    # DETECT WEB REQUEST
    # ========================================================

    def is_web_request(
        self,
        text: str
    ) -> bool:

        if not text:
            return False

        text = text.lower().strip()

        patterns = [

            r"\bsearch the web\b",
            r"\bsearch online\b",
            r"\bsearch internet\b",
            r"\bsearch for\b",
            r"\bgoogle\b",

            r"\blatest\b",
            r"\btoday\b",
            r"\bcurrently\b",
            r"\bcurrent\b",
            r"\brecent\b",
            r"\bnews\b",

            r"\bwhat happened\b",
            r"\bwhat is happening\b",

            r"\blook up\b",
            r"\bfind online\b",
            r"\bon the internet\b",

            # Telugu / transliterated
            r"search cheyyi",
            r"latest news cheppu",
            r"web lo search",

            # Hindi / transliterated
            r"search karo",
            r"online search",
            r"latest news batao",

        ]

        for pattern in patterns:

            if re.search(
                pattern,
                text,
                re.IGNORECASE
            ):

                return True

        return False

    # ========================================================
    # REMOVE COMMAND PREFIX
    # ========================================================

    def clean_query(
        self,
        text: str
    ) -> str:

        query = text.strip()

        prefixes = [

            "luna",
            "luna,",

            "search the web for",
            "search the web",
            "search online for",
            "search online",
            "search internet for",
            "search internet",

            "look up",
            "find online",
        ]

        changed = True

        while changed:

            changed = False

            lower = query.lower()

            for prefix in prefixes:

                if lower.startswith(prefix):

                    query = (
                        query[len(prefix):]
                        .strip(" ,:-")
                    )

                    changed = True

                    break

        return query.strip()

    # ========================================================
    # DETECT LANGUAGE
    # ========================================================

    def detect_language(
        self,
        text: str
    ) -> str:

        # Telugu
        if re.search(
            r"[\u0C00-\u0C7F]",
            text
        ):

            return "te"

        # Hindi / Devanagari
        if re.search(
            r"[\u0900-\u097F]",
            text
        ):

            return "hi"

        # Tamil
        if re.search(
            r"[\u0B80-\u0BFF]",
            text
        ):

            return "ta"

        # Kannada
        if re.search(
            r"[\u0C80-\u0CFF]",
            text
        ):

            return "kn"

        # Malayalam
        if re.search(
            r"[\u0D00-\u0D7F]",
            text
        ):

            return "ml"

        # Bengali
        if re.search(
            r"[\u0980-\u09FF]",
            text
        ):

            return "bn"

        # Gujarati
        if re.search(
            r"[\u0A80-\u0AFF]",
            text
        ):

            return "gu"

        # Marathi normally Devanagari
        if re.search(
            r"[\u0900-\u097F]",
            text
        ):

            return "mr"

        # Punjabi
        if re.search(
            r"[\u0A00-\u0A7F]",
            text
        ):

            return "pa"

        # Urdu
        if re.search(
            r"[\u0600-\u06FF]",
            text
        ):

            return "ur"

        return "en"

    # ========================================================
    # HANDLE WEB QUERY
    # ========================================================

    def handle(
        self,
        text: str
    ):

        if not self.is_web_request(text):

            return {
                "handled": False,
                "success": False,
                "query": text,
                "answer": "",
                "results": [],
                "language": "en",
                "error": None,
            }

        query = self.clean_query(
            text
        )

        language = self.detect_language(
            text
        )

        if not query:

            return {
                "handled": True,
                "success": False,
                "query": "",
                "answer": (
                    "Please tell me what you "
                    "want me to search for."
                ),
                "results": [],
                "language": language,
                "error": "Empty query.",
            }

        print()
        print(
            "[WEB ROUTER] Web request detected."
        )

        print(
            "[WEB ROUTER] Query:",
            query
        )

        print(
            "[WEB ROUTER] Language:",
            language
        )

        # ----------------------------------------------------
        # News requests
        # ----------------------------------------------------

        news_words = [

            "news",
            "latest news",
            "today's news",
            "today news",
            "recent news",

        ]

        is_news = any(
            word in query.lower()
            for word in news_words
        )

        if is_news:

            result = self.web.news(
                query=query,
                language=language,
                max_results=5
            )

        else:

            result = self.web.ask_web(
                query=query,
                language=language,
                max_results=5
            )

        result["handled"] = True
        result["language"] = language

        return result


# ============================================================
# ============================================================
#
#   🌙 LUNA WEB ROUTER PRO — EXTENSIONS (APPEND ONLY)
#
#   The original WebRouter above is 100% unchanged.
#   Pro overrides the four methods as guards/enrichers that
#   delegate to super() wherever the base logic is correct.
#
#   FIXES
#     • Marathi detection was UNREACHABLE — the Hindi check
#       returns "hi" for ALL Devanagari text (both scripts
#       share \u0900-\u097F), so the later "mr" branch never
#       ran. Pro disambiguates with Marathi vs Hindi marker
#       words (आहे/मध्ये/आणि vs है/में/क्या).
#     • Arabic script always mapped to "ur" — the entire
#       Arabic block matched the Urdu branch. Pro uses
#       Urdu-specific letters (ٹ ڈ ڑ ں ے گ چ پ ژ) to tell
#       them apart (same fix as the TTS and Web modules).
#     • "google" was detected but never cleaned — saying
#       "google latest cricket scores" searched for the
#       literal words "google latest…". Prefix list extended.
#     • "search for" prefix never stripped either — same
#       issue for "search for best laptops".
#     • Local questions hit the web — "what time is it
#       today", "what day is it today", "how's my battery"
#       all matched \btoday\b etc. and burned a search.
#       Pro adds a local-intent guard BEFORE routing.
#     • is_news used substring matching — "newsroom"/
#       "newspaper" inside longer phrases misrouted; Pro
#       uses word-boundary regex + transliterations.
#     • Japanese/Korean/Chinese were undetectable — the
#       router returned "en" for them even though TTS and
#       the summarizer support all three.
#
#   ADDITIONS
#     • Weather / price / score / release-date triggers
#     • Freshness inference — "today" → time_range="day",
#       "recent" → "week", passed to Pro's news/ask_web
#     • Result enrichment — "speakable" (TTS-clean answer)
#       and "sources" line added to every handled result
#     • quick_answer() — one call, plain string or None
#     • get_stats() — routed, news, local-blocked counts
#
# ============================================================
# ============================================================


class WebRouterPro(WebRouter):

    # ==================================================
    # LOCAL-INTENT GUARD
    # Phrases that LOOK webby ("today") but are
    # actually about the user's machine or clock.
    # ==================================================

    LOCAL_INTENT_PATTERNS = [
        r"what\s+(time|day)\s+is\s+it",
        r"what('s|\s+is)\s+the\s+(time|date)",
        r"(date|day)\s+today",
        r"today('s)?\s+date",
        r"my\s+(battery|cpu|ram|pc|computer|laptop|"
        r"system|disk|storage|volume|wifi|wi-fi|"
        r"screen|brightness|clipboard)",
        r"\b(screenshot|uptime)\b",
        r"system\s+(health|status)",
    ]

    # ==================================================
    # EXTRA WEB TRIGGERS
    # ==================================================

    EXTRA_PATTERNS = [
        r"\bweather\b",
        r"\btemperature\s+(in|at|of)\b",
        r"\b(price|cost)\s+of\b",
        r"\bstock\b",
        r"\bscore\b",
        r"\bwho\s+won\b",
        r"\brelease\s+date\b",
        r"\bexchange\s+rate\b",
        r"\bsamachar\b",
        r"\bkhabar\b",
        r"taza\s+khabar",
        r"aaj\s+ki\s+news",
    ]

    # ==================================================
    # MARATHI / HINDI MARKERS (Devanagari heuristic)
    # ==================================================

    MARATHI_MARKERS = [
        "आहे", "आहेत", "मध्ये", "आणि", "नाही",
        "काय", "तुम्ही", "आपण", "कसे", "किती",
        "मला", "तुला", "पण",
    ]

    HINDI_MARKERS = [
        "है", "हैं", "क्या", "कैसे", "कितना",
        "में", "और", "नहीं", "आप", "करो",
        "मुझे", "लेकिन",
    ]

    URDU_LETTERS = "ٹڈڑںےگچپژ"

    def __init__(self):

        super().__init__()

        self._stats = {
            "routed": 0,
            "news_routed": 0,
            "local_blocked": 0,
            "not_web": 0,
        }

    # ==================================================
    # FIX: DETECT LANGUAGE (all branches reachable)
    # ==================================================

    def detect_language(
        self,
        text: str,
    ) -> str:

        if not text:

            return "en"

        # ------------------------------------------
        # Arabic block — Urdu vs Arabic
        # ------------------------------------------

        if re.search(
            r"[\u0600-\u06FF]",
            text,
        ):

            if any(
                letter in text
                for letter in self.URDU_LETTERS
            ):

                return "ur"

            return "ar"

        # ------------------------------------------
        # Japanese / Korean / Chinese
        # (new — previously returned "en")
        # ------------------------------------------

        if re.search(
            r"[\u3040-\u30FF]",
            text,
        ):

            return "ja"

        if re.search(
            r"[\uAC00-\uD7AF]",
            text,
        ):

            return "ko"

        if re.search(
            r"[\u4E00-\u9FFF]",
            text,
        ):

            return "zh"

        # ------------------------------------------
        # Devanagari — Marathi vs Hindi
        # (FIX: the base returned "hi" for BOTH)
        # ------------------------------------------

        if re.search(
            r"[\u0900-\u097F]",
            text,
        ):

            marathi_hits = sum(
                1
                for word in self.MARATHI_MARKERS
                if word in text
            )

            hindi_hits = sum(
                1
                for word in self.HINDI_MARKERS
                if word in text
            )

            if marathi_hits > hindi_hits:

                return "mr"

            return "hi"

        # ------------------------------------------
        # Other Indic scripts (base logic)
        # ------------------------------------------

        return super().detect_language(
            text
        )

    # ==================================================
    # FIX: IS WEB REQUEST (guard + extra triggers)
    # ==================================================

    def is_web_request(
        self,
        text: str,
    ) -> bool:

        if not text:

            return False

        lowered = (
            str(text).lower().strip()
        )

        # ------------------------------------------
        # LOCAL-INTENT GUARD
        # "what time is it today" must never
        # reach the web just because of "today".
        # ------------------------------------------

        for pattern in (
            self.LOCAL_INTENT_PATTERNS
        ):

            if re.search(
                pattern,
                lowered,
                re.IGNORECASE,
            ):

                self._stats[
                    "local_blocked"
                ] += 1

                print(
                    "[WEB ROUTER] Local "
                    "intent — skipping web."
                )

                return False

        # ------------------------------------------
        # Base patterns
        # ------------------------------------------

        if super().is_web_request(
            text
        ):

            return True

        # ------------------------------------------
        # Extra web triggers
        # ------------------------------------------

        for pattern in (
            self.EXTRA_PATTERNS
        ):

            if re.search(
                pattern,
                lowered,
                re.IGNORECASE,
            ):

                return True

        self._stats["not_web"] += 1

        return False

    # ==================================================
    # FIX: CLEAN QUERY (google + search for)
    # ==================================================

    def clean_query(
        self,
        text: str,
    ) -> str:

        query = super().clean_query(
            text
        )

        extra_prefixes = [
            "google for",
            "google",
            "search for",
            "look up online",
            "news about",
            "latest news about",
            "on the internet",
        ]

        changed = True

        while changed:

            changed = False

            lower = (
                query.lower()
            )

            for prefix in extra_prefixes:

                if lower.startswith(
                    prefix
                ):

                    query = (
                        query[
                            len(prefix):
                        ]
                        .strip(" ,:-")
                    )

                    changed = True

                    break

        return query.strip()

    # ==================================================
    # NEWS DETECTION (word-boundary + translit)
    # ==================================================

    def is_news_query(
        self,
        query: str,
    ) -> bool:

        lowered = (
            str(query).lower()
        )

        return bool(
            re.search(
                r"\bnews\b"
                r"|\bkhabar\b"
                r"|\bsamachar\b"
                r"|\bvarthalu\b",
                lowered,
            )
        )

    # ==================================================
    # FRESHNESS INFERENCE
    # ==================================================

    @staticmethod
    def infer_time_range(
        text: str,
    ) -> Optional[str]:

        lowered = (
            str(text).lower()
        )

        if re.search(
            r"\b(today|tonight|right now|"
            r"just now|abhi|aaj)\b",
            lowered,
        ):

            return "day"

        if re.search(
            r"\b(this week|recent|latest|"
            r"yesterday|kal)\b",
            lowered,
        ):

            return "week"

        if re.search(
            r"\b(this month|past month)\b",
            lowered,
        ):

            return "month"

        if re.search(
            r"\b(this year)\b",
            lowered,
        ):

            return "year"

        return None

    # ==================================================
    # ENRICH (TTS-clean answer + citations)
    # ==================================================

    def _enrich(
        self,
        result,
    ):

        answer = str(
            result.get("answer") or ""
        )

        if answer:

            clean_answer = None

            if hasattr(
                self.web,
                "clean_for_speech",
            ):

                try:

                    clean_answer = (
                        self.web
                        .clean_for_speech(
                            answer
                        )
                    )

                except Exception:

                    clean_answer = None

            result["speakable"] = (
                clean_answer or answer
            )

        results = (
            result.get("results") or []
        )

        if results and hasattr(
            self.web,
            "sources_line",
        ):

            try:

                result["sources"] = (
                    self.web.sources_line(
                        results
                    )
                )

            except Exception:

                result["sources"] = ""

        else:

            result["sources"] = ""

        return result

    # ==================================================
    # HANDLE (enhanced flow, same result shape)
    # ==================================================

    def handle(
        self,
        text: str,
    ):

        if not self.is_web_request(
            text
        ):

            return {
                "handled": False,
                "success": False,
                "query": text,
                "answer": "",
                "results": [],
                "language": "en",
                "error": None,
            }

        query = self.clean_query(
            text
        )

        language = self.detect_language(
            text
        )

        if not query:

            return {
                "handled": True,
                "success": False,
                "query": "",
                "answer": (
                    "Please tell me what you "
                    "want me to search for."
                ),
                "results": [],
                "language": language,
                "error": "Empty query.",
            }

        print()
        print(
            "[WEB ROUTER] Web request detected."
        )

        print(
            "[WEB ROUTER] Query:",
            query
        )

        print(
            "[WEB ROUTER] Language:",
            language
        )

        time_range = self.infer_time_range(
            query
        )

        is_news = self.is_news_query(
            query
        )

        self._stats["routed"] += 1

        if is_news:

            self._stats[
                "news_routed"
            ] += 1

            # FIX: freshness now flows through —
            # "today news" searches the last DAY
            # instead of the hardcoded week.

            result = self.web.news(
                query=query,
                language=language,
                max_results=5,
                time_range=(
                    time_range or "week"
                ),
            )

        else:

            result = self.web.ask_web(
                query=query,
                language=language,
                max_results=5,
                time_range=time_range,
            )

        result["handled"] = True

        result["language"] = language

        result["is_news"] = is_news

        result["time_range"] = time_range

        return self._enrich(result)

    # ==================================================
    # ONE-CALL CONVENIENCE
    # ==================================================

    def quick_answer(
        self,
        text: str,
    ) -> Optional[str]:

        result = self.handle(text)

        if not result.get("handled"):

            return None

        return (
            result.get("speakable")
            or result.get("answer")
            or ""
        )

    # ==================================================
    # STATS
    # ==================================================

    def get_stats(self):

        return dict(self._stats)


# ------------------------------------------------------------
# DROP-IN UPGRADE
# Anything that imports WebRouter from this file now gets the
# extended version automatically (same API, smarter routing).
# Delete the next line to keep using the original.
# ------------------------------------------------------------

WebRouter = WebRouterPro


# ============================================================
# QUICK TEST (uncomment to try)
# ============================================================
#
# if __name__ == "__main__":
#
#     router = WebRouter()
#
#     # Routed to the web:
#     print(router.is_web_request("what's the weather in Vizag"))
#     print(router.is_web_request("google ipl final score"))
#
#     # Correctly blocked as local intent:
#     print(router.is_web_request("what time is it today"))
#     print(router.is_web_request("how's my battery"))
#
#     # Query cleaning now strips "google":
#     print(router.clean_query("google latest cricket scores"))
#
#     # Full answer with TTS-clean text:
#     result = router.handle("latest news about space")
#     print(result["answer"])
#     print(result.get("speakable"))
#     print(result.get("sources"))
#
#     # Language detection fixes:
#     print(router.detect_language("मी तुमच्या मदतीला आहे"))   # mr
#     print(router.detect_language("आप कैसे हैं"))              # hi
#     print(router.detect_language("مرحبا"))                    # ar