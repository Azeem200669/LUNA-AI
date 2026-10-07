import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("GROQ_MODEL")

print("🌙 LUNA - Groq Test")
print("=" * 50)
print(f"Model: {model}")

if not api_key:
    print("❌ GROQ_API_KEY not found")
    exit()

client = Groq(api_key=api_key)

try:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are LUNA, a helpful personal AI assistant."
            },
            {
                "role": "user",
                "content": "Introduce yourself in one short sentence."
            }
        ]
    )

    print("\n✅ Groq connection successful!")
    print("\nLUNA:")
    print(response.choices[0].message.content)

except Exception as e:
    print("\n❌ Groq error:")
    print(e)