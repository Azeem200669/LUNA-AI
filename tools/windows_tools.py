import os
import subprocess
import webbrowser
import time

from pathlib import Path
from datetime import datetime

import pyautogui
import psutil

from pycaw.pycaw import AudioUtilities


try:
    import pygetwindow as gw
except ImportError:
    gw = None


class WindowsTools:

    # ========================================================
    # ACTIVATE WINDOW
    # ========================================================

    @staticmethod
    def activate_window(
        title_parts,
        timeout=5.0
    ):

        if gw is None:

            return False

        start_time = time.time()

        while (
            time.time() - start_time
            < timeout
        ):

            try:

                windows = gw.getAllWindows()

                for window in windows:

                    title = (
                        window.title
                        or ""
                    ).lower()

                    for part in title_parts:

                        if part.lower() in title:

                            try:

                                if window.isMinimized:

                                    window.restore()

                                window.activate()

                                time.sleep(
                                    0.3
                                )

                                return True

                            except Exception:
                                pass

            except Exception:
                pass

            time.sleep(
                0.2
            )

        return False

    # ========================================================
    # OPEN APPLICATION
    # ========================================================

    @staticmethod
    def open_application(
        name: str
    ) -> str:

        name = (
            name
            .lower()
            .strip()
        )

        applications = {

            "notepad": [
                "notepad.exe"
            ],

            "calculator": [
                "calc.exe"
            ],

            "calc": [
                "calc.exe"
            ],

            "paint": [
                "mspaint.exe"
            ],

            "file explorer": [
                "explorer.exe"
            ],

            "explorer": [
                "explorer.exe"
            ],

            "task manager": [
                "taskmgr.exe"
            ],
        }

        # ----------------------------------------------------
        # NORMAL APPLICATIONS
        # ----------------------------------------------------

        if name in applications:

            try:

                subprocess.Popen(
                    applications[name],
                    shell=False
                )

                # Give Windows time to open it
                time.sleep(
                    1.2
                )

                # Try to activate it
                WindowsTools.activate_window(
                    [name],
                    timeout=3
                )

                return (
                    f"Opening {name}."
                )

            except Exception as error:

                return (
                    f"I couldn't open {name}: "
                    f"{error}"
                )

        # ----------------------------------------------------
        # CHROME
        # ----------------------------------------------------

        if name in [
            "chrome",
            "google chrome",
            "browser",
            "my browser",
        ]:

            chrome_paths = [

                r"C:\Program Files\Google\Chrome\Application\chrome.exe",

                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",

                os.path.expandvars(
                    r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
                ),
            ]

            for path in chrome_paths:

                if os.path.exists(path):

                    try:

                        subprocess.Popen(
                            [path]
                        )

                        time.sleep(
                            1.5
                        )

                        WindowsTools.activate_window(
                            [
                                "Google Chrome",
                                "Chrome"
                            ],
                            timeout=3
                        )

                        return (
                            "Opening Google Chrome."
                        )

                    except Exception as error:

                        return (
                            f"I couldn't open "
                            f"Google Chrome: "
                            f"{error}"
                        )

            # Browser fallback

            try:

                webbrowser.open(
                    "https://www.google.com"
                )

                time.sleep(
                    1.5
                )

                return (
                    "I couldn't find Chrome directly, "
                    "so I opened your default browser."
                )

            except Exception as error:

                return (
                    f"I couldn't open a browser: "
                    f"{error}"
                )

        # ----------------------------------------------------
        # VS CODE
        # ----------------------------------------------------

        if name in [
            "vs code",
            "visual studio code",
            "code",
        ]:

            try:

                subprocess.Popen(
                    ["code"],
                    shell=True
                )

                time.sleep(
                    1.5
                )

                WindowsTools.activate_window(
                    [
                        "Visual Studio Code",
                        "VS Code"
                    ],
                    timeout=4
                )

                return (
                    "Opening Visual Studio Code."
                )

            except Exception:

                return (
                    "I couldn't find Visual Studio Code "
                    "on your system."
                )

        return (
            f"I don't have a shortcut for "
            f"'{name}' yet."
        )

    # ========================================================
    # OPEN WEBSITE
    # ========================================================

    @staticmethod
    def open_website(
        site: str
    ) -> str:

        site = (
            site
            .lower()
            .strip()
        )

        websites = {

            "google":
                "https://www.google.com",

            "youtube":
                "https://www.youtube.com",

            "github":
                "https://github.com",

            "gmail":
                "https://mail.google.com",

            "chatgpt":
                "https://chatgpt.com",

            "instagram":
                "https://www.instagram.com",
        }

        url = websites.get(
            site
        )

        if not url:

            return (
                f"I don't have a shortcut for "
                f"{site} yet."
            )

        try:

            # ------------------------------------------------
            # Try Chrome first
            # ------------------------------------------------

            chrome_paths = [

                r"C:\Program Files\Google\Chrome\Application\chrome.exe",

                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",

                os.path.expandvars(
                    r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
                ),
            ]

            chrome_path = None

            for path in chrome_paths:

                if os.path.exists(path):

                    chrome_path = path

                    break

            if chrome_path:

                subprocess.Popen(
                    [
                        chrome_path,
                        url
                    ]
                )

            else:

                webbrowser.open(
                    url
                )

            # Give browser time to open
            time.sleep(
                1.5
            )

            WindowsTools.activate_window(
                [
                    "YouTube",
                    "Google Chrome",
                    "Chrome"
                ],
                timeout=4
            )

            return (
                f"Opening {site}."
            )

        except Exception as error:

            return (
                f"I couldn't open {site}: "
                f"{error}"
            )

    # ========================================================
    # OPEN FOLDER
    # ========================================================

    @staticmethod
    def open_folder(
        name: str
    ) -> str:

        name = (
            name
            .lower()
            .strip()
        )

        home = Path.home()

        folders = {

            "downloads":
                home / "Downloads",

            "documents":
                home / "Documents",

            "desktop":
                home / "Desktop",

            "pictures":
                home / "Pictures",

            "music":
                home / "Music",

            "videos":
                home / "Videos",
        }

        path = folders.get(
            name
        )

        if not path:

            return (
                f"I don't know the folder "
                f"'{name}'."
            )

        if not path.exists():

            return (
                f"The {name} folder does not exist."
            )

        try:

            os.startfile(
                str(path)
            )

            time.sleep(
                1.0
            )

            WindowsTools.activate_window(
                [
                    name,
                    "File Explorer"
                ],
                timeout=3
            )

            return (
                f"Opening your {name} folder."
            )

        except Exception as error:

            return (
                f"I couldn't open {name}: "
                f"{error}"
            )

    # ========================================================
    # SCREENSHOT
    # ========================================================

    @staticmethod
    def take_screenshot() -> str:

        screenshot_dir = Path(
            r"C:\Users\shaik\OneDrive\Pictures\Screenshots"
        )

        try:

            screenshot_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            # ------------------------------------------------
            # Collision-safe filename
            # ------------------------------------------------
            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S_%f"
            )

            screenshot_path = (
                screenshot_dir
                / f"luna_screenshot_{timestamp}.png"
            )

            # Extra safety: if a collision somehow occurs,
            # keep generating a unique filename.
            counter = 1

            while screenshot_path.exists():

                screenshot_path = (
                    screenshot_dir
                    / (
                        f"luna_screenshot_"
                        f"{timestamp}_{counter}.png"
                    )
                )

                counter += 1

            # ------------------------------------------------
            # Capture
            # ------------------------------------------------
            image = pyautogui.screenshot()

            image.save(
                str(screenshot_path)
            )

            return (
                f"Screenshot saved successfully to "
                f"{screenshot_path}"
            )

        except Exception as error:

            return (
                f"I couldn't take the screenshot: "
                f"{error}"
            )

    # ========================================================
    # SYSTEM INFORMATION
    # ========================================================

    @staticmethod
    def system_info() -> str:

        import platform

        try:

            system = platform.system()
            release = platform.release()
            machine = platform.machine()

            cpu = psutil.cpu_percent(
                interval=0.2
            )

            memory = psutil.virtual_memory()

            disk = psutil.disk_usage(
                "/"
            )

            return (
                f"You're running {system} "
                f"{release} on {machine}. "
                f"CPU usage is {cpu:.0f} percent, "
                f"memory usage is "
                f"{memory.percent:.0f} percent, "
                f"and disk usage is "
                f"{disk.percent:.0f} percent."
            )

        except Exception as error:

            return (
                f"I couldn't read system information: "
                f"{error}"
            )

    # ========================================================
    # VOLUME
    # ========================================================

    @staticmethod
    def get_volume():

        try:

            devices = (
                AudioUtilities.GetSpeakers()
            )

            volume = (
                devices.EndpointVolume
            )

            current = (
                volume.GetMasterVolumeLevelScalar()
            )

            return volume, current

        except Exception as error:

            print(
                f"[LUNA] Audio error: {error}"
            )

            return None, None

    # ========================================================
    # VOLUME UP
    # ========================================================

    @staticmethod
    def increase_volume() -> str:

        volume, current = (
            WindowsTools.get_volume()
        )

        if volume is None:

            return (
                "I couldn't access Windows audio."
            )

        new_volume = min(
            current + 0.10,
            1.0
        )

        volume.SetMasterVolumeLevelScalar(
            new_volume,
            None
        )

        return (
            f"Volume increased to "
            f"{int(new_volume * 100)} percent."
        )

    # ========================================================
    # VOLUME DOWN
    # ========================================================

    @staticmethod
    def decrease_volume() -> str:

        volume, current = (
            WindowsTools.get_volume()
        )

        if volume is None:

            return (
                "I couldn't access Windows audio."
            )

        new_volume = max(
            current - 0.10,
            0.0
        )

        volume.SetMasterVolumeLevelScalar(
            new_volume,
            None
        )

        return (
            f"Volume decreased to "
            f"{int(new_volume * 100)} percent."
        )

    # ========================================================
    # MUTE
    # ========================================================

    @staticmethod
    def mute() -> str:

        volume, _ = (
            WindowsTools.get_volume()
        )

        if volume is None:

            return (
                "I couldn't access Windows audio."
            )

        volume.SetMute(
            1,
            None
        )

        return (
            "I've muted the system volume."
        )

    # ========================================================
    # UNMUTE
    # ========================================================

    @staticmethod
    def unmute() -> str:

        volume, _ = (
            WindowsTools.get_volume()
        )

        if volume is None:

            return (
                "I couldn't access Windows audio."
            )

        volume.SetMute(
            0,
            None
        )

        return (
            "I've unmuted the system volume."
        )

    # ========================================================
    # LOCK
    # ========================================================

    @staticmethod
    def lock_computer() -> str:

        try:

            subprocess.run(
                [
                    "rundll32.exe",
                    "user32.dll,LockWorkStation"
                ],
                check=True
            )

            return (
                "Locking your computer."
            )

        except Exception as error:

            return (
                f"I couldn't lock the computer: "
                f"{error}"
            )

    # ========================================================
    # MOUSE POSITION
    # ========================================================

    @staticmethod
    def get_mouse_position() -> str:

        try:

            x, y = pyautogui.position()

            return (
                f"The mouse is currently at "
                f"X {x}, Y {y}."
            )

        except Exception as error:

            return (
                f"I couldn't get the mouse position: "
                f"{error}"
            )

    # ========================================================
    # MOVE MOUSE
    # ========================================================

    @staticmethod
    def move_mouse(
        x: int,
        y: int
    ) -> str:

        try:

            pyautogui.moveTo(
                x,
                y,
                duration=0.15
            )

            return (
                f"Moved the mouse to "
                f"X {x}, Y {y}."
            )

        except Exception as error:

            return (
                f"I couldn't move the mouse: "
                f"{error}"
            )

    # ========================================================
    # CLICK
    # ========================================================

    @staticmethod
    def click_mouse() -> str:

        try:

            pyautogui.click()

            return "Clicked."

        except Exception as error:

            return (
                f"I couldn't click: "
                f"{error}"
            )

    # ========================================================
    # DOUBLE CLICK
    # ========================================================

    @staticmethod
    def double_click() -> str:

        try:

            pyautogui.doubleClick(
                interval=0.1
            )

            return "Double clicked."

        except Exception as error:

            return (
                f"I couldn't double click: "
                f"{error}"
            )

    # ========================================================
    # RIGHT CLICK
    # ========================================================

    @staticmethod
    def right_click() -> str:

        try:

            pyautogui.rightClick()

            return "Right clicked."

        except Exception as error:

            return (
                f"I couldn't right click: "
                f"{error}"
            )

    # ========================================================
    # TYPE TEXT
    # ========================================================

    @staticmethod
    def type_text(
        text: str
    ) -> str:

        try:

            # Give the target window a moment
            time.sleep(
                0.5
            )

            pyautogui.write(
                text,
                interval=0.02
            )

            return (
                "I typed the requested text."
            )

        except Exception as error:

            return (
                f"I couldn't type the text: "
                f"{error}"
            )

    # ========================================================
    # PRESS KEY
    # ========================================================

    @staticmethod
    def press_key(
        key: str
    ) -> str:

        key = (
            key
            .lower()
            .strip()
        )

        if key == "esc":
            key = "escape"

        allowed_keys = {

            "enter",
            "escape",
            "tab",
            "space",
            "backspace",
            "delete",
            "home",
            "end",
            "up",
            "down",
            "left",
            "right",
            "pageup",
            "pagedown",

            "f1",
            "f2",
            "f3",
            "f4",
            "f5",
            "f6",
            "f7",
            "f8",
            "f9",
            "f10",
            "f11",
            "f12",
        }

        if key not in allowed_keys:

            return (
                f"I don't allow the key "
                f"'{key}' yet."
            )

        try:

            pyautogui.press(
                key
            )

            return (
                f"Pressed {key}."
            )

        except Exception as error:

            return (
                f"I couldn't press {key}: "
                f"{error}"
            )

    # ========================================================
    # SCROLL DOWN
    # ========================================================

    @staticmethod
    def scroll_down() -> str:

        try:

            pyautogui.scroll(
                -5
            )

            return "Scrolled down."

        except Exception as error:

            return (
                f"I couldn't scroll down: "
                f"{error}"
            )

    # ========================================================
    # SCROLL UP
    # ========================================================

    @staticmethod
    def scroll_up() -> str:

        try:

            pyautogui.scroll(
                5
            )

            return "Scrolled up."

        except Exception as error:

            return (
                f"I couldn't scroll up: "
                f"{error}"
            )

    # ========================================================
    # COPY
    # ========================================================

    @staticmethod
    def copy() -> str:

        try:

            pyautogui.hotkey(
                "ctrl",
                "c"
            )

            return "Copied."

        except Exception as error:

            return (
                f"I couldn't copy: "
                f"{error}"
            )

    # ========================================================
    # PASTE
    # ========================================================

    @staticmethod
    def paste() -> str:

        try:

            pyautogui.hotkey(
                "ctrl",
                "v"
            )

            return "Pasted."

        except Exception as error:

            return (
                f"I couldn't paste: "
                f"{error}"
            )