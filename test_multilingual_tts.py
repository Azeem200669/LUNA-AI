from voice.text_to_speech import TextToSpeech


tts = TextToSpeech()


print()
print("=" * 70)
print("             🌙 LUNA MULTILINGUAL TTS TEST")
print("=" * 70)
print()


tests = [

    # ========================================================
    # SINGLE LANGUAGES
    # ========================================================

    (
        "English",
        "en",
        "Hello, I am Luna."
    ),

    (
        "Hindi",
        "hi",
        "नमस्ते, मैं लूना हूँ।"
    ),

    (
        "Telugu",
        "te",
        "నమస్తే, నేను లూనాను."
    ),

    (
        "Tamil",
        "ta",
        "வணக்கம், நான் லூனா."
    ),

    (
        "Kannada",
        "kn",
        "ನಮಸ್ಕಾರ, ನಾನು ಲೂನಾ."
    ),

    (
        "Malayalam",
        "ml",
        "നമസ്കാരം, ഞാൻ ലൂണയാണ്."
    ),

    # ========================================================
    # MIXED LANGUAGES
    # ========================================================

    (
        "English + Telugu",
        "te",
        "Hello, నేను LUNA ని. How can I help you today?"
    ),

    (
        "English + Hindi",
        "hi",
        "Hello, मैं LUNA हूँ. How can I help you today?"
    ),

    (
        "English + Tamil",
        "ta",
        "Hello, நான் LUNA. How can I help you today?"
    ),

    (
        "English + Kannada",
        "kn",
        "Hello, ನಾನು LUNA. How can I help you today?"
    ),

    (
        "English + Malayalam",
        "ml",
        "Hello, ഞാൻ LUNA ആണ്. How can I help you today?"
    ),

]


for name, language, text in tests:

    print()
    print("-" * 70)

    print(
        f"TEST: {name}"
    )

    print(
        f"LANGUAGE: {language}"
    )

    print(
        f"TEXT: {text}"
    )

    print()

    try:

        success = tts.speak(
            text,
            language=language
        )

        print(
            f"RESULT: {success}"
        )

    except Exception as error:

        print(
            f"❌ ERROR: {error}"
        )


print()
print("=" * 70)
print("                 ✅ TEST COMPLETE")
print("=" * 70)