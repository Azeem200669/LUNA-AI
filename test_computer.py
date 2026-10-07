from tools.command_detector import CommandDetector


commands = [

    # Applications

    "please open notepad",

    "could you open calculator for me",

    "hey luna, open chrome",

    "launch my browser",

    # Websites

    "please open youtube",

    "go to github",

    # Folders

    "open my downloads folder",

    "please take me to documents",

    # Screenshot

    "luna, could you capture my screen",

    # System

    "can you show me my computer information",

    # Volume

    "make the volume louder",

    "please turn the volume down",

    "mute my computer",

    "turn the sound back on",

    # Mouse

    "where is my mouse",

    "move the mouse to x 500 y 400",

    "click",

    "double click",

    "right click",

    # Keyboard

    "type hello Luna",

    "press enter",

    "press escape",

    # Scrolling

    "scroll down",

    "scroll up",

    # Clipboard

    "copy this",

    "paste this",

]


print()
print("=" * 70)
print("             🌙 LUNA NATURAL COMMAND TEST")
print("=" * 70)


for number, command in enumerate(
    commands,
    start=1
):

    print()
    print("-" * 70)

    print(
        f"TEST {number}"
    )

    print(
        "YOU:",
        command
    )

    try:

        detected, result = (
            CommandDetector.process(
                command
            )
        )

        print(
            "DETECTED:",
            detected
        )

        print(
            "LUNA:",
            result
        )

    except Exception as error:

        print(
            "❌ ERROR:",
            error
        )


print()
print("=" * 70)
print("                 ✅ TEST COMPLETE")
print("=" * 70)