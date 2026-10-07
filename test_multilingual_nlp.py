from nlp.nlp_engine import NLPEngine


nlp = NLPEngine()


tests = [

    # ========================================================
    # ENGLISH
    # ========================================================

    "open chrome",

    "take a screenshot",

    # ========================================================
    # TELUGU
    # ========================================================

    "లూనా క్రోమ్ ఓపెన్ చెయ్యి",

    "లూనా స్క్రీన్ షాట్ తీసుకో",

    # ========================================================
    # HINDI
    # ========================================================

    "लूना क्रोम खोलो",

    "स्क्रीनशॉट लो",

    # ========================================================
    # TAMIL
    # ========================================================

    "லூனா குரோம் திற",

    # ========================================================
    # MIXED ENGLISH + TELUGU
    # ========================================================

    "Luna, Chrome open cheyyi",

    "Luna, YouTube ki vellandi",

    "please Chrome open cheyyi",

    # ========================================================
    # MIXED ENGLISH + HINDI
    # ========================================================

    "Luna Chrome open karo",

    "YouTube kholo",

    # ========================================================
    # MIXED ENGLISH + TAMIL
    # ========================================================

    "Luna Chrome open pannu",

]


print()
print("=" * 75)
print("        🌐 LUNA MULTILINGUAL SEMANTIC NLP TEST")
print("=" * 75)


for index, text in enumerate(
    tests,
    start=1
):

    print()
    print("-" * 75)

    print(
        f"TEST {index}"
    )

    print(
        f"INPUT: {text}"
    )

    try:

        result = nlp.analyze(
            text
        )

        print(
            f"LANGUAGE: "
            f"{result['language_name']}"
        )

        print(
            f"INTENT: "
            f"{result['intent']}"
        )

        print(
            f"ENTITY: "
            f"{result['entity']}"
        )

        print(
            f"CONFIDENCE: "
            f"{result['confidence']:.2f}"
        )

        print(
            f"SOURCE: "
            f"{result['source']}"
        )

        print(
            f"COMMAND: "
            f"{result['is_command']}"
        )

    except Exception as error:

        print(
            f"❌ ERROR: {error}"
        )


print()
print("=" * 75)
print("                 ✅ TEST COMPLETE")
print("=" * 75)