from groq import Groq

import config


class GroqModel:

    def __init__(self):

        if not config.GROQ_API_KEY:

            raise ValueError(
                "GROQ_API_KEY is missing in .env"
            )

        self.client = Groq(
            api_key=config.GROQ_API_KEY
        )

    def generate(
        self,
        message: str
    ) -> str:

        response = self.client.chat.completions.create(

            model=config.GROQ_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": config.LUNA_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": message
                }
            ],

            temperature=0.7,

            max_tokens=500
        )

        return (
            response
            .choices[0]
            .message
            .content
            .strip()
        )