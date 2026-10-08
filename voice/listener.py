import sounddevice as sd


def list_microphones():
    print("\n🎙️ Available microphones")
    print("=" * 60)

    devices = sd.query_devices()

    for index, device in enumerate(devices):
        if device["max_input_channels"] > 0:
            print(
                f"[{index}] {device['name']}"
            )


def test_microphone(duration=5):

    print("\n🎙️ LUNA Microphone Test")
    print("=" * 60)

    print(f"Recording for {duration} seconds...")
    print("Speak normally into your microphone.\n")

    recording = sd.rec(
        int(duration * 16000),
        samplerate=16000,
        channels=1,
        dtype="float32"
    )

    sd.wait()

    volume = abs(recording).max()

    print("\n✅ Recording completed.")
    print(f"Maximum microphone volume: {volume:.4f}")

    if volume < 0.01:
        print("⚠️ Very low microphone input detected.")
    else:
        print("🎙️ Microphone is receiving audio.")


if __name__ == "__main__":

    list_microphones()

    input("\nPress ENTER to start microphone test...")

    test_microphone()