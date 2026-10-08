import re

from tools.windows_tools import WindowsTools


class CommandDetector:

    # ========================================================
    # NORMALIZE
    # ========================================================

    @staticmethod
    def normalize(message: str) -> str:

        text = message.lower().strip()

        # Remove common assistant addressing
        prefixes = [
            "hey luna",
            "hi luna",
            "hello luna",
            "luna",
        ]

        changed = True

        while changed:

            changed = False

            for prefix in prefixes:

                if text.startswith(prefix):

                    text = text[len(prefix):].strip()

                    changed = True

        # Remove polite phrases

        text = re.sub(
            r"\bplease\b",
            "",
            text
        )

        text = re.sub(
            r"\bfor me\b",
            "",
            text
        )

        text = re.sub(
            r"\bcan you\b",
            "",
            text
        )

        text = re.sub(
            r"\bcould you\b",
            "",
            text
        )

        text = re.sub(
            r"\bwould you\b",
            "",
            text
        )

        text = re.sub(
            r"\bwill you\b",
            "",
            text
        )

        text = re.sub(
            r"\bkindly\b",
            "",
            text
        )

        # Clean duplicate whitespace

        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        return text

    # ========================================================
    # PROCESS
    # ========================================================

    @staticmethod
    def process(message: str):

        text = CommandDetector.normalize(
            message
        )

        # ====================================================
        # SCREENSHOT
        # ====================================================

        screenshot_phrases = [

            "take a screenshot",
            "capture screenshot",
            "capture the screen",
            "capture my screen",
            "take screenshot",
            "screenshot my screen",
            "save a screenshot",
            "take a picture of the screen",
        ]

        if any(
            phrase in text
            for phrase in screenshot_phrases
        ):

            return (
                True,
                WindowsTools.take_screenshot()
            )

        # ====================================================
        # SYSTEM INFORMATION
        # ====================================================

        system_phrases = [

            "system information",
            "system info",
            "computer information",
            "pc information",
            "computer specs",
            "pc specs",
            "my system",
            "my computer",
            "computer status",
            "how is my computer",
        ]

        if any(
            phrase in text
            for phrase in system_phrases
        ):

            return (
                True,
                WindowsTools.system_info()
            )

        # ====================================================
        # VOLUME UP
        # ====================================================

        volume_up_phrases = [

            "increase volume",
            "turn volume up",
            "volume up",
            "make volume louder",
            "make it louder",
            "increase the sound",
            "turn the sound up",
            "louder",
        ]

        if any(
            phrase in text
            for phrase in volume_up_phrases
        ):

            return (
                True,
                WindowsTools.increase_volume()
            )

        # ====================================================
        # VOLUME DOWN
        # ====================================================

        volume_down_phrases = [

            "decrease volume",
            "turn volume down",
            "volume down",
            "make volume quieter",
            "make it quieter",
            "decrease the sound",
            "turn the sound down",
            "quieter",
        ]

        if any(
            phrase in text
            for phrase in volume_down_phrases
        ):

            return (
                True,
                WindowsTools.decrease_volume()
            )

        # ====================================================
        # MUTE
        # ====================================================

        mute_phrases = [

            "mute",
            "mute volume",
            "mute the volume",
            "mute my computer",
            "mute the computer",
            "turn off the sound",
            "silence the computer",
        ]

        if any(
            phrase == text
            or phrase in text
            for phrase in mute_phrases
        ):

            return (
                True,
                WindowsTools.mute()
            )

        # ====================================================
        # UNMUTE
        # ====================================================

        unmute_phrases = [

            "unmute",
            "unmute volume",
            "unmute the volume",
            "unmute my computer",
            "unmute the computer",
            "turn the sound back on",
        ]

        if any(
            phrase == text
            or phrase in text
            for phrase in unmute_phrases
        ):

            return (
                True,
                WindowsTools.unmute()
            )

        # ====================================================
        # LOCK
        # ====================================================

        lock_phrases = [

            "lock computer",
            "lock my computer",
            "lock the computer",
            "lock pc",
            "lock my pc",
            "lock the pc",
            "lock workstation",
        ]

        if any(
            phrase in text
            for phrase in lock_phrases
        ):

            return (
                True,
                WindowsTools.lock_computer()
            )

        # ====================================================
        # MOUSE POSITION
        # ====================================================

        if (
            "mouse position" in text
            or "mouse location" in text
            or "where is my mouse" in text
            or "where's my mouse" in text
        ):

            return (
                True,
                WindowsTools.get_mouse_position()
            )

        # ====================================================
        # CLICK
        # ====================================================

        if text in [
            "click",
            "click here",
            "mouse click",
            "left click",
            "do a click",
        ]:

            return (
                True,
                WindowsTools.click_mouse()
            )

        # ====================================================
        # DOUBLE CLICK
        # ====================================================

        if (
            text in [
                "double click",
                "double-click",
                "do a double click",
            ]
        ):

            return (
                True,
                WindowsTools.double_click()
            )

        # ====================================================
        # RIGHT CLICK
        # ====================================================

        if text in [
            "right click",
            "right-click",
            "mouse right click",
            "do a right click",
        ]:

            return (
                True,
                WindowsTools.right_click()
            )

        # ====================================================
        # TYPE TEXT
        # ====================================================

        type_patterns = [

            r"^type\s+(.+)$",

            r"^write\s+(.+)$",

            r"^enter\s+(.+)$",

            r"^type this\s+(.+)$",

            r"^write this\s+(.+)$",
        ]

        for pattern in type_patterns:

            match = re.search(
                pattern,
                message,
                re.IGNORECASE
            )

            if match:

                typed_text = (
                    match.group(1).strip()
                )

                return (
                    True,
                    WindowsTools.type_text(
                        typed_text
                    )
                )

        # ====================================================
        # PRESS KEY
        # ====================================================

        key_pattern = re.search(
            r"""
            ^(?:press|hit)
            \s+
            (enter|escape|esc|tab|space|
             backspace|delete|home|end|
             up|down|left|right|
             pageup|pagedown|
             f1|f2|f3|f4|f5|f6|
             f7|f8|f9|f10|f11|f12)
            $
            """,
            text,
            re.IGNORECASE | re.VERBOSE
        )

        if key_pattern:

            key = key_pattern.group(
                1
            )

            return (
                True,
                WindowsTools.press_key(
                    key
                )
            )

        # ====================================================
        # SCROLL DOWN
        # ====================================================

        if (
            "scroll down" in text
            or "scroll downward" in text
            or "scroll lower" in text
            or "go down" == text
        ):

            return (
                True,
                WindowsTools.scroll_down()
            )

        # ====================================================
        # SCROLL UP
        # ====================================================

        if (
            "scroll up" in text
            or "scroll upward" in text
            or "scroll higher" in text
            or "go up" == text
        ):

            return (
                True,
                WindowsTools.scroll_up()
            )

        # ====================================================
        # COPY
        # ====================================================

        if text in [
            "copy",
            "copy this",
            "copy that",
            "copy it",
        ]:

            return (
                True,
                WindowsTools.copy()
            )

        # ====================================================
        # PASTE
        # ====================================================

        if text in [
            "paste",
            "paste this",
            "paste that",
            "paste it",
        ]:

            return (
                True,
                WindowsTools.paste()
            )

        # ====================================================
        # MOVE MOUSE
        # ====================================================

        mouse_patterns = [

            r"mouse\s+to\s+x\s*(\d+)\s+y\s*(\d+)",

            r"move\s+mouse\s+to\s+x\s*(\d+)\s+y\s*(\d+)",

            r"move\s+the\s+mouse\s+to\s+x\s*(\d+)\s+y\s*(\d+)",

            r"put\s+mouse\s+at\s+x\s*(\d+)\s+y\s*(\d+)",
        ]

        for pattern in mouse_patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                x = int(
                    match.group(1)
                )

                y = int(
                    match.group(2)
                )

                return (
                    True,
                    WindowsTools.move_mouse(
                        x,
                        y
                    )
                )

        # ====================================================
        # FOLDER
        # ====================================================

        folder_pattern = re.search(
            r"""
            (?:open|show|go\s+to|
             take\s+me\s+to|access)
            \s+
            (?:my\s+)?
            (downloads|documents|desktop|
             pictures|music|videos)
            """,
            text,
            re.IGNORECASE | re.VERBOSE
        )

        if folder_pattern:

            folder = folder_pattern.group(
                1
            )

            return (
                True,
                WindowsTools.open_folder(
                    folder
                )
            )

        # ====================================================
        # WEBSITE
        # ====================================================

        website_pattern = re.search(
            r"""
            (?:open|launch|visit|go\s+to|
             take\s+me\s+to)
            \s+
            (google|youtube|github|gmail|
             chatgpt|instagram)
            """,
            text,
            re.IGNORECASE | re.VERBOSE
        )

        if website_pattern:

            site = website_pattern.group(
                1
            )

            return (
                True,
                WindowsTools.open_website(
                    site
                )
            )

        # ====================================================
        # APPLICATION
        # ====================================================

        application_pattern = re.search(
            r"""
            (?:open|launch|start|run|load)
            \s+
            (google\s+chrome|chrome|
             my\s+browser|
             vs\s+code|visual\s+studio\s+code|
             code|
             notepad|
             calculator|calc|
             paint|
             file\s+explorer|explorer|
             task\s+manager)
            """,
            text,
            re.IGNORECASE | re.VERBOSE
        )

        if application_pattern:

            application = (
                application_pattern
                .group(1)
            )

            # "my browser" means Chrome
            if application == "my browser":
                application = "chrome"

            return (
                True,
                WindowsTools.open_application(
                    application
                )
            )

        # ====================================================
        # NOT A COMPUTER COMMAND
        # ====================================================

        return (
            False,
            None
        )