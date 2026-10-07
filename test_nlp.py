from nlp.nlp_engine import NLPEngine


nlp = NLPEngine()


tests = [

    # -------------------------------
    # English
    # -------------------------------

    "open chrome",

    "please open notepad",

    "take a screenshot",

    "increase volume",

    # -------------------------------
    # Telugu
    # -------------------------------

    "లూనా క్రోమ్ ఓపెన్ చెయ్యి",

    "లూనా స్క్రీన్ షాట్ తీసుకో",

    # -------------------------------
    # Hindi
    # -------------------------------

    "लूना क्रोम खोलो",

    "स्क्रीनशॉट लो",

    # -------------------------------
    # Tamil
    # -------------------------------

    "லூனா குரோம் திற",

    # -------------------------------
    # Mixed
    # -------------------------------

    "Luna, Chrome open cheyyi",

    "Chrome open karo",

    "Luna, YouTube ki vellandi",

    "please Chrome open cheyyi",

]


print()
print("=" * 70)
print(
    "             🌐 LUNA MULTILINGUAL NLP TEST"
)
print("=" * 70)


for number, text in enumerate(
    tests,
    start=1
):

    print()
    print("-" * 70)

    print(
        f"TEST {number}"
    )

    print(
        "INPUT:",
        text
    )

    result = nlp.analyze(
        text
    )

    print(
        "LANGUAGE:",
        result["language_name"]
    )

    print(
        "INTENT:",
        result["intent"]
    )

    print(
        "ENTITY:",
        result["entity"]
    )

    print(
        "COMMAND:",
        result["is_command"]
    )


print()
print("=" * 70)
print("                  ✅ NLP TEST COMPLETE")
print("=" * 70)