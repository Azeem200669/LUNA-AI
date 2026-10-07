from core.agent import LunaAgent


agent = LunaAgent()


tests = [


    "open chrome chahiye",

    "open notepad and type hello Luna",

]


print()
print("=" * 70)
print(
    "              🌙 LUNA AGENT TEST"
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
        "YOU:",
        text
    )

    try:

        response = agent.chat(
            text,
            model="groq"
        )

        print(
            "\nLUNA:",
            response
        )

    except Exception as error:

        print(
            "\n❌ ERROR:",
            error
        )


print()
print("=" * 70)
print(
    "                 ✅ TEST COMPLETE"
)
print("=" * 70)