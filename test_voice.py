from voice.speech_to_text import SpeechToText


stt = SpeechToText()

print("=" * 50)
print("        🌙 LUNA SPEECH TEST")
print("=" * 50)

text = stt.listen()

if text:
    print("\nLUNA received:")
    print(text)
else:
    print("\nNo text received.")