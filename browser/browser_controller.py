import os
import socket
import subprocess
import time

from pathlib import Path
from urllib.parse import quote_plus

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)


class BrowserController:

    def __init__(self):

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        self.chrome_process = None
        self.started = False

        # ====================================================
        # LUNA CHROME PROFILE
        # ====================================================

        self.profile_dir = (
            Path.home()
            / "AppData"
            / "Local"
            / "LUNA"
            / "ChromeProfile"
        )

        self.debug_port = 9222

    # ========================================================
    # FIND GOOGLE CHROME
    # ========================================================

    def _find_chrome(self):

        paths = [
            Path(
                r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            ),
            Path(
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ),
            Path(
                os.path.expandvars(
                    r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
                )
            ),
        ]

        for path in paths:

            if path.exists():

                print(
                    f"[BROWSER] Google Chrome found: {path}"
                )

                return str(path)

        return None

    # ========================================================
    # CHECK DEBUG PORT
    # ========================================================

    def _port_open(
        self,
        host="127.0.0.1",
        port=9222
    ):

        try:

            with socket.create_connection(
                (host, port),
                timeout=0.3
            ):

                return True

        except OSError:

            return False

    # ========================================================
    # START REAL GOOGLE CHROME
    # ========================================================

    def _start_chrome(self):

        chrome_path = self._find_chrome()

        if not chrome_path:

            raise RuntimeError(
                "Google Chrome executable was not found."
            )

        self.profile_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        command = [
            chrome_path,
            f"--remote-debugging-port={self.debug_port}",
            f"--user-data-dir={self.profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-popup-blocking",
            "--start-maximized",
        ]

        print(
            "[BROWSER] Starting REAL Google Chrome..."
        )

        self.chrome_process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )

        for _ in range(50):

            if self._port_open(
                port=self.debug_port
            ):

                print(
                    "[BROWSER] Chrome debugging ready."
                )

                return True

            time.sleep(0.1)

        raise RuntimeError(
            "Chrome started, but remote debugging "
            "did not become available."
        )

    # ========================================================
    # CONNECT PLAYWRIGHT TO CHROME
    # ========================================================

    def _connect(self):

        self.playwright = (
            sync_playwright().start()
        )

        print(
            "[BROWSER] Connecting to Google Chrome..."
        )

        self.browser = (
            self.playwright.chromium.connect_over_cdp(
                f"http://127.0.0.1:{self.debug_port}"
            )
        )

        contexts = self.browser.contexts

        if contexts:

            self.context = contexts[0]

        else:

            self.context = (
                self.browser.new_context(
                    viewport=None
                )
            )

        pages = self.context.pages

        if pages:

            self.page = pages[-1]

        else:

            self.page = (
                self.context.new_page()
            )

        self.started = True

        print(
            "[BROWSER] Connected to Google Chrome."
        )

        return True

    # ========================================================
    # START
    # ========================================================

    def start(self):

        if (
            self.started
            and self.page
            and not self.page.is_closed()
        ):

            return True

        try:

            print()
            print("=" * 40)
            print("      🌙 LUNA GOOGLE CHROME CONTROL")
            print("=" * 40)

            if not self._port_open(
                port=self.debug_port
            ):

                self._start_chrome()

            self._connect()

            return True

        except Exception as error:

            print(
                f"[BROWSER] Start error: {error}"
            )

            self.close()

            return False

    # ========================================================
    # ENSURE STARTED
    # ========================================================

    def ensure_started(self):

        if (
            self.started
            and self.page
            and not self.page.is_closed()
        ):

            return True

        return self.start()

    # ========================================================
    # OPEN CHROME
    # ========================================================

    def open_chrome(self):

        if self.ensure_started():

            return "Google Chrome is ready."

        return (
            "I couldn't start Google Chrome."
        )

    # ========================================================
    # WAIT
    # ========================================================

    def wait(
        self,
        seconds=1
    ):

        time.sleep(seconds)

    # ========================================================
    # OPEN URL
    # ========================================================

    def open_url(
        self,
        url: str
    ):

        if not url:

            return "The URL is missing."

        if not self.ensure_started():

            return (
                "Google Chrome is unavailable."
            )

        try:

            self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=15000
            )

            return (
                f"Opened {url} in Google Chrome."
            )

        except Exception as error:

            return (
                f"I couldn't open the URL: {error}"
            )

    # ========================================================
    # GOOGLE SEARCH
    # ========================================================

    def google_search(
        self,
        query: str
    ):

        if not query:

            return (
                "Please tell me what to search for."
            )

        if not self.ensure_started():

            return (
                "Google Chrome is unavailable."
            )

        try:

            url = (
                "https://www.google.com/search?q="
                + quote_plus(query)
            )

            self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=15000
            )

            return (
                f"Searching Google for {query}."
            )

        except Exception as error:

            return (
                f"I couldn't search Google: {error}"
            )

    # ========================================================
    # YOUTUBE SEARCH
    # ========================================================

    def youtube_search(
        self,
        query: str
    ):

        if not query:

            return (
                "Please tell me what to search for."
            )

        if not self.ensure_started():

            return (
                "Google Chrome is unavailable."
            )

        try:

            url = (
                "https://www.youtube.com/results?search_query="
                + quote_plus(query)
            )

            self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=15000
            )

            return (
                f"Searching YouTube for {query}."
            )

        except Exception as error:

            return (
                f"I couldn't search YouTube: {error}"
            )

    # ========================================================
    # INTERACTIVE GOOGLE SEARCH
    # ========================================================

    def google_search_interactive(
        self,
        query: str
    ):

        if not query:

            return (
                "Please tell me what to search for."
            )

        if not self.ensure_started():

            return (
                "Google Chrome is unavailable."
            )

        try:

            self.page.goto(
                "https://www.google.com",
                wait_until="domcontentloaded",
                timeout=15000
            )

            search_box = self.find_element(
                [
                    'textarea[name="q"]',
                    'input[name="q"]',
                    'input[aria-label*="Search"]',
                ],
                timeout=7000
            )

            if search_box is None:

                return (
                    "I couldn't find Google's search box."
                )

            search_box.fill(query)
            search_box.press("Enter")

            try:

                self.page.wait_for_load_state(
                    "domcontentloaded",
                    timeout=10000
                )

            except PlaywrightTimeoutError:

                pass

            return (
                f"Google search completed for {query}."
            )

        except Exception as error:

            return (
                f"Google interaction failed: {error}"
            )

    # ========================================================
    # INTERACTIVE YOUTUBE SEARCH
    # ========================================================

    def youtube_search_interactive(
        self,
        query: str
    ):

        if not query:

            return (
                "Please tell me what to search for."
            )

        if not self.ensure_started():

            return (
                "Google Chrome is unavailable."
            )

        try:

            self.page.goto(
                "https://www.youtube.com",
                wait_until="domcontentloaded",
                timeout=15000
            )

            search_box = self.find_element(
                [
                    'input[name="search_query"]',
                    'input#search',
                    'input[placeholder*="Search"]',
                ],
                timeout=10000
            )

            if search_box is None:

                return (
                    "I couldn't find YouTube's search box."
                )

            search_box.fill(query)
            search_box.press("Enter")

            try:

                self.page.wait_for_load_state(
                    "domcontentloaded",
                    timeout=10000
                )

            except PlaywrightTimeoutError:

                pass

            time.sleep(0.8)

            return (
                f"YouTube search completed for {query}."
            )

        except Exception as error:

            return (
                f"YouTube interaction failed: {error}"
            )

    # ========================================================
    # FIND ELEMENT
    # ========================================================

    def find_element(
        self,
        selectors,
        timeout=5000
    ):

        if not self.ensure_started():

            return None

        if isinstance(
            selectors,
            str
        ):

            selectors = [selectors]

        for selector in selectors:

            try:

                locator = (
                    self.page
                    .locator(selector)
                    .first
                )

                locator.wait_for(
                    state="visible",
                    timeout=timeout
                )

                return locator

            except Exception:

                continue

        return None

    # ========================================================
    # CLICK ELEMENT
    # ========================================================

    def click_element(
        self,
        selectors,
        timeout=5000
    ):

        element = self.find_element(
            selectors,
            timeout
        )

        if element is None:

            return (
                "I couldn't find the element to click."
            )

        try:

            element.click(
                timeout=timeout
            )

            return (
                "Clicked the requested element."
            )

        except Exception as error:

            return (
                f"I couldn't click the element: {error}"
            )

    # ========================================================
    # CLICK TEXT
    # ========================================================

    def click_text(
        self,
        text,
        timeout=5000
    ):

        if not text:

            return (
                "The text to click is missing."
            )

        if not self.ensure_started():

            return (
                "Google Chrome is unavailable."
            )

        try:

            locator = (
                self.page
                .get_by_text(
                    str(text),
                    exact=True
                )
                .first
            )

            locator.wait_for(
                state="visible",
                timeout=timeout
            )

            locator.click(
                timeout=timeout
            )

            return (
                f"Clicked '{text}'."
            )

        except Exception:

            try:

                locator = (
                    self.page
                    .get_by_role(
                        "link",
                        name=str(text)
                    )
                    .first
                )

                locator.wait_for(
                    state="visible",
                    timeout=timeout
                )

                locator.click(
                    timeout=timeout
                )

                return (
                    f"Clicked '{text}'."
                )

            except Exception as error:

                return (
                    f"I couldn't click '{text}': {error}"
                )

    # ========================================================
    # CLICK FIRST YOUTUBE RESULT
    # ========================================================

    def click_first_youtube_result(self):

        if not self.ensure_started():

            return (
                "Google Chrome is unavailable."
            )

        try:

            selectors = [
                "ytd-video-renderer a#video-title",
                "ytd-video-renderer h3",
                "ytd-rich-item-renderer a#video-title",
            ]

            video = self.find_element(
                selectors,
                timeout=10000
            )

            if video is None:

                return (
                    "I couldn't find a YouTube video result."
                )

            title = ""

            try:

                title = (
                    video.get_attribute("title")
                    or video.inner_text()
                )

            except Exception:

                title = "the first video"

            video.click()

            return (
                f"Opening {title}."
            )

        except Exception as error:

            return (
                f"I couldn't open the first "
                f"YouTube result: {error}"
            )

    # ========================================================
    # CLICK FIRST GOOGLE RESULT
    # ========================================================

    def click_first_google_result(self):

        if not self.ensure_started():

            return (
                "Google Chrome is unavailable."
            )

        try:

            result = (
                self.page
                .locator("a:has(h3)")
                .first
            )

            result.wait_for(
                state="visible",
                timeout=10000
            )

            title = ""

            try:

                title = (
                    result
                    .locator("h3")
                    .inner_text()
                )

            except Exception:

                title = "the first search result"

            result.click()

            return (
                f"Opening {title}."
            )

        except Exception as error:

            return (
                f"I couldn't open the first "
                f"Google result: {error}"
            )

    # ========================================================
    # TYPE INTO BROWSER
    # ========================================================

    def type_into_element(
        self,
        selectors,
        text,
        timeout=5000
    ):

        if text is None:

            return (
                "There is no text to enter."
            )

        element = self.find_element(
            selectors,
            timeout
        )

        if element is None:

            return (
                "I couldn't find the input field."
            )

        try:

            element.fill(
                str(text),
                timeout=timeout
            )

            return (
                "Entered the requested text."
            )

        except Exception as error:

            return (
                f"I couldn't enter the text: {error}"
            )

    # ========================================================
    # PRESS KEY
    # ========================================================

    def press_key(
        self,
        key
    ):

        if not self.ensure_started():

            return (
                "Google Chrome is unavailable."
            )

        try:

            self.page.keyboard.press(
                str(key)
            )

            return (
                f"Pressed {key}."
            )

        except Exception as error:

            return (
                f"I couldn't press {key}: {error}"
            )

    # ========================================================
    # READ PAGE TEXT
    # ========================================================

    def get_page_text(
        self,
        max_length=7000
    ):

        if not self.ensure_started():

            return (
                "Google Chrome is unavailable."
            )

        try:

            text = (
                self.page
                .locator("body")
                .inner_text(timeout=7000)
            )

            text = " ".join(
                text.split()
            )

            if len(text) > max_length:

                text = (
                    text[:max_length]
                    + "..."
                )

            return text

        except Exception as error:

            return (
                f"I couldn't read the webpage: {error}"
            )

    # ========================================================
    # READ PAGE FOR AI
    # ========================================================

    def read_page_for_ai(
        self,
        max_length=7000
    ):

        if not self.ensure_started():

            return {
                "success": False,
                "title": "",
                "url": "",
                "text": "",
                "error": "Browser unavailable.",
            }

        try:

            title = self.page.title()

            url = self.page.url

            text = (
                self.page
                .locator("body")
                .inner_text(timeout=7000)
            )

            text = " ".join(
                text.split()
            )

            if len(text) > max_length:

                text = (
                    text[:max_length]
                    + "..."
                )

            return {
                "success": True,
                "title": title,
                "url": url,
                "text": text,
                "error": None,
            }

        except Exception as error:

            return {
                "success": False,
                "title": "",
                "url": "",
                "text": "",
                "error": str(error),
            }

    # ========================================================
    # GET VISIBLE LINKS
    # ========================================================

    def get_visible_links(
        self,
        limit=20
    ):

        if not self.ensure_started():

            return []

        try:

            links = (
                self.page
                .locator("a")
                .all()
            )

            results = []

            for link in links:

                if len(results) >= limit:

                    break

                try:

                    if not link.is_visible():

                        continue

                    text = (
                        link
                        .inner_text()
                        .strip()
                    )

                    href = (
                        link
                        .get_attribute("href")
                    )

                    if text and href:

                        results.append(
                            {
                                "text": text,
                                "href": href,
                            }
                        )

                except Exception:

                    continue

            return results

        except Exception as error:

            print(
                f"[BROWSER] Link extraction error: {error}"
            )

            return []

    # ========================================================
    # GET YOUTUBE RESULT TITLES
    # ========================================================

    def get_result_titles(
        self,
        limit=10
    ):

        if not self.ensure_started():

            return []

        try:

            results = []

            selectors = [
                "ytd-video-renderer",
                "ytd-rich-item-renderer",
            ]

            for selector in selectors:

                items = (
                    self.page
                    .locator(selector)
                    .all()
                )

                for item in items:

                    if len(results) >= limit:

                        break

                    try:

                        title_locator = (
                            item
                            .locator("#video-title")
                            .first
                        )

                        title = (
                            title_locator
                            .inner_text()
                            .strip()
                        )

                        if title:

                            results.append(
                                title
                            )

                    except Exception:

                        continue

                if results:

                    break

            return results

        except Exception as error:

            print(
                f"[BROWSER] Result extraction error: {error}"
            )

            return []

    # ========================================================
    # GET PAGE TITLE
    # ========================================================

    def get_title(self):

        if not self.ensure_started():

            return (
                "Google Chrome is unavailable."
            )

        try:

            return self.page.title()

        except Exception as error:

            return (
                f"Couldn't get page title: {error}"
            )

    # ========================================================
    # GET CURRENT URL
    # ========================================================

    def get_url(self):

        if not self.ensure_started():

            return (
                "Google Chrome is unavailable."
            )

        try:

            return self.page.url

        except Exception as error:

            return (
                f"Couldn't get current URL: {error}"
            )

    # ========================================================
    # GO BACK
    # ========================================================

    def back(self):

        if not self.ensure_started():

            return (
                "Google Chrome is unavailable."
            )

        try:

            self.page.go_back(
                wait_until="domcontentloaded",
                timeout=10000
            )

            return "Going back."

        except PlaywrightTimeoutError:

            return "Going back."

        except Exception as error:

            return (
                f"I couldn't go back: {error}"
            )

    # ========================================================
    # GO FORWARD
    # ========================================================

    def forward(self):

        if not self.ensure_started():

            return (
                "Google Chrome is unavailable."
            )

        try:

            self.page.go_forward(
                wait_until="domcontentloaded",
                timeout=10000
            )

            return "Going forward."

        except PlaywrightTimeoutError:

            return "Going forward."

        except Exception as error:

            return (
                f"I couldn't go forward: {error}"
            )

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh(self):

        if not self.ensure_started():

            return (
                "Google Chrome is unavailable."
            )

        try:

            self.page.reload(
                wait_until="domcontentloaded",
                timeout=10000
            )

            return "Refreshing the page."

        except PlaywrightTimeoutError:

            return "Refreshing the page."

        except Exception as error:

            return (
                f"I couldn't refresh the page: {error}"
            )

    # ========================================================
    # NEW TAB
    # ========================================================

    def new_tab(self):

        if not self.ensure_started():

            return (
                "Google Chrome is unavailable."
            )

        try:

            self.page = (
                self.context.new_page()
            )

            return "Opened a new Chrome tab."

        except Exception as error:

            return (
                f"I couldn't open a new tab: {error}"
            )

    # ========================================================
    # CLOSE TAB
    # ======================# ============================================================
# ============================================================
#
#   🌙 LUNA LAPTOP CONTROL  —  NEW FEATURES (APPEND ONLY)
#
#   Nothing above this line was changed.
#   Everything below gives LUNA control over the laptop:
#   battery, volume, brightness, screenshots, webcam,
#   wi-fi, media keys, power, apps, mouse, keyboard,
#   clipboard, notifications and system health.
#
# ============================================================
# ============================================================

import ctypes
import datetime
import re
import shutil

from ctypes import cast, POINTER

# ------------------------------------------------------------
# OPTIONAL LIBRARIES — LUNA still works if any are missing.
#   pip install psutil pyautogui screen-brightness-control pyperclip plyer opencv-python pycaw comtypes Pillow
# ------------------------------------------------------------

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    PYAUTOGUI_OK = True
except ImportError:
    PYAUTOGUI_OK = False

try:
    from PIL import ImageGrab
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False

try:
    import screen_brightness_control as sbc
    BRIGHTNESS_OK = True
except ImportError:
    BRIGHTNESS_OK = False

try:
    import pyperclip
    CLIPBOARD_OK = True
except ImportError:
    CLIPBOARD_OK = False

try:
    from plyer import notification
    NOTIFICATIONS_OK = True
except ImportError:
    NOTIFICATIONS_OK = False

try:
    import cv2
    WEBCAM_OK = True
except ImportError:
    WEBCAM_OK = False

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    PYCAW_OK = True
except ImportError:
    PYCAW_OK = False

# ------------------------------------------------------------
# WINDOWS VIRTUAL KEY CODES (zero libraries needed)
# ------------------------------------------------------------

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3


class LaptopController:

    # ========================================================
    # APP LAUNCH MAP
    # ========================================================

    APP_COMMANDS = {
        "notepad": "notepad",
        "calculator": "calc",
        "calc": "calc",
        "paint": "mspaint",
        "explorer": "explorer",
        "files": "explorer",
        "file explorer": "explorer",
        "task manager": "taskmgr",
        "cmd": "cmd",
        "command prompt": "cmd",
        "powershell": "powershell",
        "settings": "ms-settings:",
        "windows settings": "ms-settings:",
        "word": "winword",
        "excel": "excel",
        "powerpoint": "powerpnt",
        "spotify": "spotify:",
        "discord": "discord:",
        "camera": "microsoft.windows.camera:",
        "clock": "ms-clock:",
        "store": "ms-windows-store:",
        "mail": "outlookmail:",
    }

    def __init__(self):

        self.screenshot_dir = (
            Path.home() / "Pictures" / "LUNA_Screenshots"
        )

        self.webcam_dir = (
            Path.home() / "Pictures" / "LUNA_Webcam"
        )

    # ========================================================
    # START
    # ========================================================

    def start(self):

        print()
        print("=" * 40)
        print("      💻 LUNA LAPTOP CONTROL")
        print("=" * 40)

        self.show_capabilities()

        return True

    # ========================================================
    # SHOW CAPABILITIES
    # ========================================================

    def show_capabilities(self):

        items = [
            ("Battery status", PSUTIL_OK),
            ("CPU / RAM / disk monitor", PSUTIL_OK),
            ("Uptime", PSUTIL_OK),
            ("Volume control", True),
            ("Media keys (play/pause/next)", True),
            ("Brightness control", BRIGHTNESS_OK),
            ("Screenshots", PYAUTOGUI_OK or PILLOW_OK),
            ("Webcam photos", WEBCAM_OK),
            ("Wi-Fi info & scan", True),
            ("Power (lock/sleep/restart)", True),
            ("App launcher", True),
            ("Global typing / mouse", PYAUTOGUI_OK),
            ("Clipboard", CLIPBOARD_OK),
            ("Notifications", NOTIFICATIONS_OK),
        ]

        print()

        for name, available in items:

            mark = "✅" if available else "➖ (pip install needed)"

            print(f"   {mark}  {name}")

        print()

        return True

    # ========================================================
    # HELPERS
    # ========================================================

    def _tap_key(self, virtual_key, presses=1):

        for _ in range(presses):

            ctypes.windll.user32.keybd_event(virtual_key, 0, 0, 0)
            ctypes.windll.user32.keybd_event(virtual_key, 0, 2, 0)

    def _extract_number(self, text):

        match = re.search(r"\d+", str(text))

        if match:

            return int(match.group())

        return None

    # ========================================================
    # BATTERY
    # ========================================================

    def battery_status(self):

        if not PSUTIL_OK:

            return "Battery reading needs psutil. Run: pip install psutil"

        battery = psutil.sensors_battery()

        if battery is None:

            return "I couldn't find a battery on this machine."

        percent = round(battery.percent)

        if battery.power_plugged:

            return f"The laptop is charging and is at {percent} percent."

        left = battery.secsleft

        if left in (
            psutil.POWER_TIME_UNLIMITED,
            psutil.POWER_TIME_UNKNOWN,
        ) or left <= 0:

            return f"The laptop is on battery at {percent} percent."

        hours = int(left // 3600)
        minutes = int((left % 3600) // 60)

        return (
            f"The laptop is on battery at {percent} percent, "
            f"with about {hours} hours and {minutes} minutes left."
        )

    # ========================================================
    # SYSTEM HEALTH
    # ========================================================

    def system_status(self):

        if not PSUTIL_OK:

            return "System monitoring needs psutil. Run: pip install psutil"

        cpu = round(psutil.cpu_percent(interval=1))
        ram = round(psutil.virtual_memory().percent)
        disk = round(psutil.disk_usage("C:\\").percent)

        return (
            f"CPU is at {cpu} percent. "
            f"Memory is at {ram} percent. "
            f"Disk C is at {disk} percent."
        )

    def uptime(self):

        if not PSUTIL_OK:

            return "Uptime needs psutil. Run: pip install psutil"

        seconds = int(time.time() - psutil.boot_time())

        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        parts = []

        if days:
            parts.append(f"{days} days")
        if hours:
            parts.append(f"{hours} hours")

        parts.append(f"{minutes} minutes")

        return "The laptop has been on for " + ", ".join(parts) + "."

    def screen_resolution(self):

        width = ctypes.windll.user32.GetSystemMetrics(0)
        height = ctypes.windll.user32.GetSystemMetrics(1)

        return f"The screen is {width} by {height} pixels."

    # ========================================================
    # VOLUME (keyboard taps = zero dependencies)
    # ========================================================

    def volume_up(self, steps=5):

        self._tap_key(VK_VOLUME_UP, steps)

        return "Turning the volume up."

    def volume_down(self, steps=5):

        self._tap_key(VK_VOLUME_DOWN, steps)

        return "Turning the volume down."

    def mute(self):

        self._tap_key(VK_VOLUME_MUTE)

        return "Toggled mute."

    def set_volume(self, percent):

        percent = max(0, min(100, int(percent)))

        if not PYCAW_OK:

            return "Exact volume needs pycaw. Run: pip install pycaw comtypes"

        try:

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_,
                CLSCTX_ALL,
                None,
            )
            volume = cast(
                interface,
                POINTER(IAudioEndpointVolume),
            )
            volume.SetMasterVolumeLevelScalar(
                percent / 100.0,
                None,
            )

            return f"Volume set to {percent} percent."

        except Exception as error:

            return f"I couldn't set the volume: {error}"

    def volume_status(self):

        if not PYCAW_OK:

            return (
                "I can raise, lower or mute the volume. "
                "Exact level needs: pip install pycaw comtypes"
            )

        try:

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_,
                CLSCTX_ALL,
                None,
            )
            volume = cast(
                interface,
                POINTER(IAudioEndpointVolume),
            )

            level = int(round(volume.GetMasterVolumeLevelScalar() * 100))

            if volume.GetMute():

                return f"Volume is muted. Level is {level} percent."

            return f"Volume is at {level} percent."

        except Exception as error:

            return f"I couldn't read the volume: {error}"

    # ========================================================
    # BRIGHTNESS
    # ========================================================

    def _current_brightness(self):

        level = sbc.get_brightness()

        if isinstance(level, list):

            return int(level[0])

        return int(level)

    def brightness_set(self, percent):

        if not BRIGHTNESS_OK:

            return "Brightness needs: pip install screen-brightness-control"

        percent = max(0, min(100, int(percent)))

        try:

            sbc.set_brightness(percent)

            return f"Brightness set to {percent} percent."

        except Exception as error:

            return f"I couldn't change brightness: {error}"

    def brightness_up(self, step=10):

        if not BRIGHTNESS_OK:

            return "Brightness needs: pip install screen-brightness-control"

        return self.brightness_set(
            self._current_brightness() + step
        )

    def brightness_down(self, step=10):

        if not BRIGHTNESS_OK:

            return "Brightness needs: pip install screen-brightness-control"

        return self.brightness_set(
            self._current_brightness() - step
        )

    def brightness_status(self):

        if not BRIGHTNESS_OK:

            return "Brightness needs: pip install screen-brightness-control"

        return f"Brightness is at {self._current_brightness()} percent."

    # ========================================================
    # SCREENSHOT & WEBCAM
    # ========================================================

    def take_screenshot(self):

        self.screenshot_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.screenshot_dir / f"luna_screenshot_{stamp}.png"

        try:

            if PYAUTOGUI_OK:

                pyautogui.screenshot(str(path))

            elif PILLOW_OK:

                ImageGrab.grab().save(str(path))

            else:

                return "Screenshots need pyautogui or Pillow."

            return f"Screenshot saved to {path}."

        except Exception as error:

            return f"I couldn't take a screenshot: {error}"

    def take_webcam_photo(self):

        if not WEBCAM_OK:

            return "Webcam needs opencv. Run: pip install opencv-python"

        self.webcam_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        camera = cv2.VideoCapture(0)
        frame = None

        try:

            for _ in range(8):

                ok, current = camera.read()

                if ok:

                    frame = current

                time.sleep(0.05)

        finally:

            camera.release()

        if frame is None:

            return "I couldn't access the webcam."

        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.webcam_dir / f"luna_webcam_{stamp}.png"

        cv2.imwrite(str(path), frame)

        return f"Webcam photo saved to {path}."

    # ========================================================
    # WI-FI
    # ========================================================

    def wifi_status(self):

        try:

            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            output = result.stdout

            if "disconnected" in output.lower():

                return "Wi-Fi is not connected."

            ssid = None
            signal = None

            for line in output.splitlines():

                clean = line.strip()

                if (
                    clean.startswith("SSID")
                    and ":" in clean
                    and not clean.startswith("BSSID")
                ):

                    ssid = clean.split(":", 1)[1].strip()

                if clean.startswith("Signal") and ":" in clean:

                    signal = clean.split(":", 1)[1].strip()

            if ssid:

                if signal:

                    return f"Connected to {ssid}, signal strength {signal}."

                return f"Connected to {ssid}."

            return "Wi-Fi is not connected."

        except Exception as error:

            return f"I couldn't check Wi-Fi: {error}"

    def list_wifi_networks(self, limit=10):

        try:

            result = subprocess.run(
                ["netsh", "wlan", "show", "networks"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            networks = []

            for line in result.stdout.splitlines():

                clean = line.strip()

                if (
                    clean.startswith("SSID")
                    and ":" in clean
                    and not clean.startswith("BSSID")
                ):

                    name = clean.split(":", 1)[1].strip()

                    if name:

                        networks.append(name)

            if not networks:

                return "I couldn't find any Wi-Fi networks."

            top = networks[:limit]

            return "Nearby networks: " + ", ".join(top) + "."

        except Exception as error:

            return f"I couldn't scan Wi-Fi: {error}"

    # ========================================================
    # MEDIA KEYS (works for Spotify, YouTube, etc.)
    # ========================================================

    def media_play_pause(self):

        self._tap_key(VK_MEDIA_PLAY_PAUSE)

        return "Toggled play and pause."

    def media_next(self):

        self._tap_key(VK_MEDIA_NEXT_TRACK)

        return "Skipping to the next track."

    def media_previous(self):

        self._tap_key(VK_MEDIA_PREV_TRACK)

        return "Going to the previous track."

    def media_stop(self):

        self._tap_key(VK_MEDIA_STOP)

        return "Stopping playback."

    # ========================================================
    # POWER
    # ========================================================

    def lock_pc(self):

        subprocess.Popen(
            ["rundll32.exe", "user32.dll,LockWorkStation"],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        return "Locking the laptop."

    def sleep_pc(self):

        subprocess.Popen(
            ["rundll32.exe", "powrprof.dll,SetSuspendState 0,1,0"],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        return "Putting the laptop to sleep."

    def restart_pc(self):

        subprocess.run(["shutdown", "/r", "/t", "5"])

        return "Restarting the laptop in 5 seconds."

    def shutdown_pc(self):

        subprocess.run(["shutdown", "/s", "/t", "5"])

        return "Shutting down the laptop in 5 seconds."

    def abort_shutdown(self):

        try:

            subprocess.run(["shutdown", "/a"])

            return "Shutdown cancelled."

        except Exception:

            return "There is no shutdown to cancel."

    # ========================================================
    # APPS / TYPING / MOUSE / CLIPBOARD
    # ========================================================

    def open_app(self, name):

        name = (name or "").strip().lower()

        if not name:

            return "Which app should I open?"

        command = self.APP_COMMANDS.get(name)

        if command:

            subprocess.Popen(
                f'start "" "{command}"',
                shell=True,
            )

            return f"Opening {name}."

        exe = shutil.which(name)

        if exe:

            subprocess.Popen(
                f'start "" "{exe}"',
                shell=True,
            )

            return f"Opening {name}."

        return f"I don't know how to open {name} on this laptop."

    def type_text(self, text):

        if not PYAUTOGUI_OK:

            return "Typing needs pyautogui. Run: pip install pyautogui"

        pyautogui.write(str(text), interval=0.02)

        return f"Typed: {text}"

    def press_laptop_key(self, key):

        if not PYAUTOGUI_OK:

            return "Key presses need pyautogui."

        pyautogui.press(str(key))

        return f"Pressed {key}."

    def press_hotkey(self, *keys):

        if not PYAUTOGUI_OK:

            return "Hotkeys need pyautogui."

        pyautogui.hotkey(*[k.lower() for k in keys])

        return "Pressed the hotkey."

    def move_mouse(self, x, y):

        if not PYAUTOGUI_OK:

            return "Mouse control needs pyautogui."

        pyautogui.moveTo(int(x), int(y), duration=0.3)

        return f"Moved the mouse to {x}, {y}."

    def mouse_click(self, button="left"):

        if not PYAUTOGUI_OK:

            return "Mouse control needs pyautogui."

        pyautogui.click(button=button)

        return "Clicked."

    def mouse_scroll(self, amount):

        if not PYAUTOGUI_OK:

            return "Mouse control needs pyautogui."

        pyautogui.scroll(int(amount))

        return "Scrolled."

    def copy_to_clipboard(self, text):

        if not CLIPBOARD_OK:

            return "Clipboard needs pyperclip. Run: pip install pyperclip"

        pyperclip.copy(str(text))

        return "Copied to the clipboard."

    def read_clipboard(self):

        if not CLIPBOARD_OK:

            return "Clipboard needs pyperclip. Run: pip install pyperclip"

        content = pyperclip.paste()

        if not content:

            return "The clipboard is empty."

        return f"The clipboard says: {content}"

    def notify(self, title, message):

        if not NOTIFICATIONS_OK:

            return "Notifications need plyer. Run: pip install plyer"

        try:

            notification.notify(
                title=str(title)[:64],
                message=str(message)[:200],
                timeout=5,
                app_name="LUNA",
            )

            return "Notification sent."

        except Exception as error:

            return f"I couldn't send a notification: {error}"

    # ========================================================
    # ONE-COMMAND DISPATCHER (natural phrases → features)
    # ========================================================

    def run_command(self, text):

        text = (text or "").lower().strip()

        if not text:

            return "I didn't hear a laptop command."

        # --- battery ---
        if "battery" in text:
            return self.battery_status()

        # --- screenshot ---
        if "screenshot" in text or "screen shot" in text:
            return self.take_screenshot()

        # --- webcam ---
        if any(p in text for p in ("webcam", "selfie", "take a photo", "take my photo")):
            return self.take_webcam_photo()

        # --- volume ---
        if "volume" in text or "louder" in text or "quieter" in text:
            if "mute" in text:
                return self.mute()
            if "up" in text or "louder" in text or "increase" in text:
                return self.volume_up()
            if "down" in text or "quieter" in text or "decrease" in text:
                return self.volume_down()
            number = self._extract_number(text)
            if number is not None:
                return self.set_volume(number)
            return self.volume_status()

        # --- brightness ---
        if "brightness" in text or "dim" in text:
            if "up" in text or "brighter" in text or "increase" in text:
                return self.brightness_up()
            if "down" in text or "dimmer" in text or "darker" in text or "decrease" in text:
                return self.brightness_down()
            number = self._extract_number(text)
            if number is not None:
                return self.brightness_set(number)
            return self.brightness_status()

        # --- system health ---
        if any(w in text for w in ("cpu", "ram", "memory", "disk", "storage", "performance")):
            return self.system_status()

        if "uptime" in text or "how long has" in text:
            return self.uptime()

        if "resolution" in text:
            return self.screen_resolution()

        # --- wi-fi ---
        if "wi-fi" in text or "wifi" in text:
            if any(w in text for w in ("list", "scan", "nearby", "available")):
                return self.list_wifi_networks()
            return self.wifi_status()

        # --- media ---
        if any(p in text for p in ("next song", "next track", "next video", "skip")):
            return self.media_next()
        if any(p in text for p in ("previous song", "previous track", "last song")):
            return self.media_previous()
        if "pause" in text or "resume" in text or "play music" in text:
            return self.media_play_pause()

        # --- power ---
        if "abort" in text and ("shutdown" in text or "shut down" in text):
            return self.abort_shutdown()
        if "lock" in text:
            return self.lock_pc()
        if "sleep" in text or "hibernate" in text:
            return self.sleep_pc()
        if "restart" in text or "reboot" in text:
            return self.restart_pc()
        if "shutdown" in text or "shut down" in text:
            return self.shutdown_pc()

        # --- clipboard ---
        if "clipboard" in text:
            if "copy" in text:
                rest = text.split("copy", 1)[1].replace("to clipboard", "").strip()
                if rest:
                    return self.copy_to_clipboard(rest)
                return "Tell me what to copy after the word copy."
            return self.read_clipboard()

        # --- open apps ---
        for prefix in ("open ", "launch ", "start "):
            if text.startswith(prefix):
                return self.open_app(text[len(prefix):])

        # --- typing / keys ---
        if text.startswith("type "):
            return self.type_text(text[5:])
        if "press enter" in text:
            return self.press_laptop_key("enter")

        # --- mouse ---
        if "scroll up" in text:
            return self.mouse_scroll(400)
        if "scroll down" in text:
            return self.mouse_scroll(-400)
        if "click" in text:
            return self.mouse_click()

        return "I don't have that laptop command yet."


# ============================================================
# HOW TO USE WITH LUNA (example — do not auto-run)
# ============================================================
#
#   laptop = LaptopController()
#   laptop.start()
#   reply = laptop.run_command("what's my battery level")
#
# ==============================================================================================

    def close_tab(self):

        if not self.page:

            return (
                "There is no active Chrome tab."
            )

        try:

            self.page.close()

            pages = self.context.pages

            if pages:

                self.page = pages[-1]

            else:

                self.page = (
                    self.context.new_page()
                )

            return "Closed the current Chrome tab."

        except Exception as error:

            return (
                f"I couldn't close the tab: {error}"
            )

    # ========================================================
    # CLOSE EVERYTHING
    # ========================================================

    def close(self):

        try:

            if self.browser:

                self.browser.close()

        except Exception:
            pass

        try:

            if self.playwright:

                self.playwright.stop()

        except Exception:
            pass

        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

        self.started = False