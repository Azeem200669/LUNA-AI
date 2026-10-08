from google import genai

import config


class GeminiModel:

    def __init__(self):
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing in .env")

        self.client = genai.Client(
            api_key=config.GEMINI_API_KEY
        )

    def generate(self, message: str) -> str:

        response = self.client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=message
        )

        return response.text