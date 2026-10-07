from voice.speech_to_text import SpeechToText


def main():

    print()
    print("=" * 60)
    print("              🌙 LUNA SPEECH TEST")
    print("=" * 60)
    print()
    print("Speak naturally.")
    print("Say 'stop testing' to exit.")
    print()

    stt = SpeechToText()

    while True:

        text = stt.listen()

        if not text:
            continue

        print()
        print(
            "FINAL:",
            text
        )

        command = text.lower().strip()

        if command in [
            "exit",
            "quit",
            "stop testing",
        ]:

            print(
                "🌙 LUNA speech test stopped."
            )

            break


if __name__ == "__main__":
    main()