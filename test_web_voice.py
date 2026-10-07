from core.web_response import WebResponse
from voice.text_to_speech import TextToSpeech


web = WebResponse()

tts = TextToSpeech()


tests = [

    {
        "text": "Luna, search the web for the latest AI news",
        "language": "en",
    },

    {
        "text": "Luna, what are the latest developments in artificial intelligence",
        "language": "en",
    },

    {
        "text": "AI గురించి తాజా వార్తలు చెప్పు",
        "language": "te",
    },

    {
        "text": "AI की ताज़ा खबरें बताओ",
        "language": "hi",
    },

]


print()
print("=" * 80)
print("           🌙 LUNA WEB + VOICE TEST")
print("=" * 80)


for index, item in enumerate(
    tests,
    start=1
):

    user_text = item["text"]

    print()
    print("=" * 80)

    print(
        f"TEST {index}"
    )

    print(
        f"USER: {user_text}"
    )

    print("=" * 80)

    # ========================================================
    # WEB
    # ========================================================

    result = web.get_speakable_answer(
        user_text
    )

    if not result["handled"]:

        print(
            "❌ Web request was not detected."
        )

        continue

    if not result["success"]:

        print(
            "❌ Web search failed."
        )

        print(
            result.get(
                "error"
            )
        )

        continue

    # ========================================================
    # TEXT ANSWER
    # ========================================================

    print()
    print(
        "🤖 LUNA ANSWER:"
    )

    print()

    print(
        result["answer"]
    )

    # ========================================================
    # SPEAKABLE ANSWER
    # ========================================================

    speak_text = (
        result["speakable_answer"]
    )

    language = (
        result["language"]
    )

    print()
    print(
        "🔊 SPEAKING:"
    )

    print(
        speak_text
    )

    print()
    print(
        "LANGUAGE:",
        language
    )

    # ========================================================
    # TTS
    # ========================================================

    try:

        tts.speak(
            speak_text,
            language=language
        )

        print(
            "✅ Voice response completed."
        )

    except Exception as error:

        print(
            "❌ TTS ERROR:"
        )

        print(
            error
        )


print()
print("=" * 80)
print("              ✅ WEB + VOICE TEST COMPLETE")
print("=" * 80)