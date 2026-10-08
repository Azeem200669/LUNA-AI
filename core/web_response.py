from web.web_router import WebRouter


class WebResponse:

    def __init__(self):

        self.router = WebRouter()

    # ========================================================
    # HANDLE USER MESSAGE
    # ========================================================

    def handle(
        self,
        user_text: str
    ):

        result = self.router.handle(
            user_text
        )

        if not result.get(
            "handled",
            False
        ):

            return {
                "handled": False,
                "success": False,
                "answer": "",
                "language": "en",
                "sources": [],
                "error": None,
            }

        return {
            "handled": True,

            "success": result.get(
                "success",
                False
            ),

            "answer": result.get(
                "answer",
                ""
            ),

            "language": result.get(
                "language",
                "en"
            ),

            "sources": result.get(
                "results",
                []
            ),

            "query": result.get(
                "query",
                user_text
            ),

            "error": result.get(
                "error"
            ),
        }

    # ========================================================
    # CREATE SPEAKABLE ANSWER
    # ========================================================

    def get_speakable_answer(
        self,
        user_text: str
    ):

        result = self.handle(
            user_text
        )

        if not result["handled"]:

            return result

        if not result["success"]:

            return result

        answer = (
            result["answer"]
            or
            "I found some information, "
            "but I couldn't generate the answer."
        )

        # Keep spoken answer reasonably concise.
        answer = self._clean_for_speech(
            answer
        )

        result["speakable_answer"] = answer

        return result

    # ========================================================
    # CLEAN FOR TTS
    # ========================================================

    def _clean_for_speech(
        self,
        text: str
    ):

        if not text:

            return ""

        text = text.replace(
            "```",
            ""
        )

        text = text.replace(
            "**",
            ""
        )

        text = text.replace(
            "__",
            ""
        )

        # Remove markdown links but keep link text.
        import re

        text = re.sub(
            r"\[([^\]]+)\]\([^)]+\)",
            r"\1",
            text
        )

        # Remove excessive whitespace.
        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()