from models.gemini import GeminiModel
from models.groq import GroqModel


class ModelRouter:

    def __init__(self):

        self.gemini = None
        self.groq = None

    # ========================================================
    # LAZY LOAD GEMINI
    # ========================================================

    def get_gemini(self):

        if self.gemini is None:
            self.gemini = GeminiModel()

        return self.gemini

    # ========================================================
    # LAZY LOAD GROQ
    # ========================================================

    def get_groq(self):

        if self.groq is None:
            self.groq = GroqModel()

        return self.groq

    # ========================================================
    # ASK
    # ========================================================

    def ask(
        self,
        message: str,
        model="auto"
    ):

        model = model.lower().strip()

        # ----------------------------------------------------
        # AUTO
        # ----------------------------------------------------

        if model == "auto":

            # Try Gemini first

            try:

                print(
                    "[LUNA] Trying Gemini..."
                )

                return self.get_gemini().generate(
                    message
                )

            except Exception as gemini_error:

                print(
                    f"[LUNA] Gemini unavailable: "
                    f"{gemini_error}"
                )

                print(
                    "[LUNA] Switching to Groq..."
                )

            # Try Groq

            try:

                return self.get_groq().generate(
                    message
                )

            except Exception as groq_error:

                print(
                    f"[LUNA] Groq unavailable: "
                    f"{groq_error}"
                )

                return (
                    "I'm unable to reach my AI services "
                    "right now."
                )

        # ----------------------------------------------------
        # GEMINI
        # ----------------------------------------------------

        if model == "gemini":

            return self.get_gemini().generate(
                message
            )

        # ----------------------------------------------------
        # GROQ
        # ----------------------------------------------------

        if model == "groq":

            return self.get_groq().generate(
                message
            )

        return "Unknown AI model."