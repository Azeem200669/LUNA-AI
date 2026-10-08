import re
import time
from typing import Dict, Any


class FastRouter:

    """
    LUNA low-latency command router.

    IMPORTANT PERFORMANCE RULE:

    1. Route using local pattern matching.
    2. Do NOT load FileRouter/WebRouter unless needed.
    3. Browser detection happens before generic web detection.
    4. File detection is intentionally narrow.
    5. Normal AI questions should return immediately.
    """

    def __init__(self):

        self._file_router = None
        self._web_router = None

        # ====================================================
        # COMPILED LOCAL PATTERNS
        # ====================================================

        self.file_patterns = [
            re.compile(
                r"\b(find|locate)\b.*"
                r"(\.(py|pdf|docx|xlsx|pptx|txt|png|jpg|jpeg|csv|zip|mp3|mp4|msi|exe)\b)",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(open)\b.*"
                r"\.(py|pdf|docx|xlsx|pptx|txt|png|jpg|jpeg|csv|zip|mp3|mp4|msi|exe)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(find|search)\b.*"
                r"\bfiles?\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(show|list)\b.*\bfiles?\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\bwhat files\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\bfiles?\b.*\b(downloads?|documents?|desktop|"
                r"pictures?|videos?|music|luna project|luna folder)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(python|pdf|word|excel|powerpoint|"
                r"text|image)\s+files?\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\bopen\b\s+the\s+latest\s+"
                r"(pdf|word|excel|powerpoint|text|image|file)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\bfind files containing\b",
                re.IGNORECASE
            ),
        ]

        self.computer_patterns = [
            re.compile(
                r"\bopen\s+(chrome|google chrome|"
                r"notepad|calculator|paint|explorer|"
                r"file explorer|task manager|vs code)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\bopen\s+(downloads?|documents?|desktop|"
                r"pictures?|music|videos?)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(take|capture)\s+(a\s+)?screenshot\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(system info|system information)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(increase|decrease)\s+volume\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\bvolume\s+(up|down)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(mute|unmute)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\block\s+(the\s+)?(computer|pc|laptop)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(mouse position|get mouse position)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(move|click|double click|right click)\b"
                r".*\b(mouse|cursor)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\bscroll\s+(up|down)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(copy|paste)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\bpress\s+(enter|escape|esc|tab|space|"
                r"backspace|delete|home|end)\b",
                re.IGNORECASE
            ),
        ]

        self.browser_patterns = [
            re.compile(
                r"\b(open|go to)\s+(youtube|google|github|"
                r"gmail|chatgpt|instagram)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(search)\b.*\b(youtube|google)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(search)\s+(youtube|google)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(go to)\s+(youtube|google|github|gmail|"
                r"chatgpt|instagram)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(open)\s+the\s+first\s+result\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(click)\s+.*\b(first|second|third)\s+result\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(read)\s+(this\s+)?webpage\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(read)\s+(the\s+)?page\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\bgo\s+back\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\bgo\s+forward\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\brefresh\s+(the\s+)?page\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\bnew\s+tab\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\bclose\s+tab\b",
                re.IGNORECASE
            ),

            # Common transliterated requests
            re.compile(
                r"\byoutube\b.*\b(search|open|vell|ki)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(chrome|google)\b.*\b(search|open|ki|vell)\b",
                re.IGNORECASE
            ),
        ]

        self.web_patterns = [
            re.compile(
                r"\b(latest|today|current|currently|recent)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(news|headlines)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(search the web|search online|search internet)\b",
                re.IGNORECASE
            ),

            # Generic "search for <topic>" that does NOT mention a browser
            # platform (those are caught by browser_patterns first).
            re.compile(
                r"\bsearch\s+for\b(?!.*\b(youtube|google|github|gmail|"
                r"chatgpt|instagram)\b)",
                re.IGNORECASE
            ),

            re.compile(
                r"\blook\s+up\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\bfind\s+online\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\bon\s+the\s+internet\b",
                re.IGNORECASE
            ),

            # Telugu transliteration
            re.compile(
                r"\bweb\s+lo\s+search\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\blatest\s+news\s+cheppu\b",
                re.IGNORECASE
            ),

            # Hindi transliteration
            re.compile(
                r"\blatest\s+news\s+batao\b",
                re.IGNORECASE
            ),
        ]

        # ====================================================
        # COMPILED AI INDICATORS
        # ====================================================

        self.ai_patterns = [
            re.compile(
                r"\b(explain|what is|what are|how does|"
                r"why does|tell me about|describe)\b",
                re.IGNORECASE
            ),

            re.compile(
                r"\b(help me understand|teach me|"
                r"compare|difference between)\b",
                re.IGNORECASE
            ),
        ]

    # ========================================================
    # ROUTE
    # ========================================================

    def route(
        self,
        text: str
    ) -> Dict[str, Any]:

        started = time.perf_counter()

        if not text:

            return self._result(
                "unknown",
                0.0,
                "empty_input",
                started
            )

        clean = self._clean(
            text
        )

        # ====================================================
        # ORDER MATTERS
        # ====================================================

        # 1. COMPUTER
        #
        # "open Chrome" must NOT become a file command.
        # ====================================================

        if self._matches(
            self.computer_patterns,
            clean
        ):

            return self._result(
                "computer",
                0.99,
                "local_computer_command",
                started
            )

        # ====================================================
        # 2. BROWSER
        #
        # "search YouTube..." must NOT become generic web.
        # ====================================================

        if self._matches(
            self.browser_patterns,
            clean
        ):

            return self._result(
                "browser",
                0.99,
                "browser_command",
                started
            )

        # ====================================================
        # 3. WEB
        # ====================================================

        if self._matches(
            self.web_patterns,
            clean
        ):

            return self._result(
                "web",
                0.98,
                "web_request",
                started
            )

        # ====================================================
        # 4. FILE
        #
        # Only narrow file patterns are allowed.
        # ====================================================

        if self._matches(
            self.file_patterns,
            clean
        ):

            return self._result(
                "file",
                0.98,
                "file_request",
                started
            )

        # ====================================================
        # 5. AI
        #
        # Normal conversational / knowledge request.
        # ====================================================

        return self._result(
            "ai",
            0.90,
            "normal_ai_request",
            started
        )

    # ========================================================
    # CLEAN WAKE WORD
    # ========================================================

    def _clean(
        self,
        text: str
    ) -> str:

        value = str(
            text
        ).strip()

        value = re.sub(
            r"^\s*luna\s*[,;:!\-]?\s*",
            "",
            value,
            flags=re.IGNORECASE
        )

        return value.strip()

    # ========================================================
    # MATCH
    # ========================================================

    @staticmethod
    def _matches(
        patterns,
        text: str
    ) -> bool:

        for pattern in patterns:

            if pattern.search(
                text
            ):

                return True

        return False

    # ========================================================
    # RESULT
    # ========================================================

    def _result(
        self,
        route: str,
        confidence: float,
        reason: str,
        started: float
    ) -> Dict[str, Any]:

        elapsed_ms = (
            time.perf_counter()
            - started
        ) * 1000

        return {
            "route": route,
            "confidence": confidence,
            "reason": reason,
            "execution_ms": round(
                elapsed_ms,
                3
            ),
            "router": None,
        }

    # ========================================================
    # GET FILE ROUTER
    # ========================================================

    def get_file_router(self):

        if self._file_router is None:

            from core.file_router import FileRouter

            self._file_router = FileRouter()

        return self._file_router

    # ========================================================
    # GET WEB ROUTER
    # ========================================================

    def get_web_router(self):

        if self._web_router is None:

            from core.web_router import WebRouter

            self._web_router = WebRouter()

        return self._web_router

    # ========================================================
    # FILE CHECK
    # ========================================================

    def is_file(
        self,
        text: str
    ) -> bool:

        return (
            self.route(text)["route"]
            == "file"
        )

    # ========================================================
    # COMPUTER CHECK
    # ========================================================

    def is_computer(
        self,
        text: str
    ) -> bool:

        return (
            self.route(text)["route"]
            == "computer"
        )

    # ========================================================
    # BROWSER CHECK
    # ========================================================

    def is_browser(
        self,
        text: str
    ) -> bool:

        return (
            self.route(text)["route"]
            == "browser"
        )

    # ========================================================
    # WEB CHECK
    # ========================================================

    def is_web(
        self,
        text: str
    ) -> bool:

        return (
            self.route(text)["route"]
            == "web"
        )

    # ========================================================
    # AI CHECK
    # ========================================================

    def is_ai(
        self,
        text: str
    ) -> bool:

        return (
            self.route(text)["route"]
            == "ai"
        )