from core.agent import LunaAgent


def main():

    print()
    print("=" * 50)
    print("              🌙 LUNA")
    print("        Personal AI Assistant")
    print("=" * 50)
    print()

    luna = LunaAgent()

    print("LUNA is ready.")
    print("Type 'exit' to quit.")
    print()

    while True:

        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("LUNA: Goodbye.")
            break

        response = luna.chat(
            user_input,
            model="auto"
        )

        print()
        print("LUNA:", response)
        print()


if __name__ == "__main__":
    main()