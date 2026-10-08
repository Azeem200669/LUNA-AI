import time
import threading

from browser.browser_controller import BrowserController
from tools.windows_tools import WindowsTools


class ActionExecutor:

    # ========================================================
    # THREAD LOCAL BROWSER
    # ========================================================

    _local = threading.local()

    # ========================================================
    # GET BROWSER
    # ========================================================

    @classmethod
    def get_browser(cls):

        browser = getattr(
            cls._local,
            "browser",
            None
        )

        if browser is None:

            print(
                "[BROWSER] Creating browser "
                "inside current worker thread."
            )

            browser = BrowserController()

            cls._local.browser = browser

        return browser

    # ========================================================
    # BROWSER ACTION CHECK
    # ========================================================

    @staticmethod
    def is_browser_action(
        action_name
    ):

        return action_name in {

            "browser_open",

            "google_search",

            "youtube_search",

            "google_search_interactive",

            "youtube_search_interactive",

            "browser_click",

            "browser_click_text",

            "browser_click_first_result",

            "browser_type",

            "browser_press",

            "browser_read_page",

            "browser_read_results",

            "browser_read_links",

            "browser_title",

            "browser_url",

            "browser_back",

            "browser_forward",

            "browser_refresh",

            "browser_new_tab",

            "browser_close_tab",
        }

    # ========================================================
    # EXECUTE PLAN
    # ========================================================

    @classmethod
    def execute(
        cls,
        plan,
        progress_callback=None
    ):

        actions = plan.get(
            "actions",
            []
        )

        if not isinstance(
            actions,
            list
        ):

            return []

        results = []

        total = len(
            actions
        )

        for index, action in enumerate(
            actions,
            start=1
        ):

            if not isinstance(
                action,
                dict
            ):

                continue

            next_action = None

            if index < total:

                next_action = actions[index]

            print()
            print(
                f"[LUNA] Step {index}/{total}"
            )

            print(
                f"[LUNA] Action: {action}"
            )

            try:

                result = (
                    cls.execute_action(
                        action,
                        next_action
                    )
                )

            except Exception as error:

                result = (
                    f"Action failed: {error}"
                )

            results.append(
                {
                    "step": index,
                    "action": action,
                    "result": result,
                }
            )

            print(
                f"[LUNA] Result: {result}"
            )

            if progress_callback:

                try:

                    progress_callback(
                        index,
                        total,
                        action,
                        result
                    )

                except Exception as error:

                    print(
                        f"[LUNA] Progress callback error: "
                        f"{error}"
                    )

            if index < total:

                cls.wait_between_actions(
                    action,
                    next_action
                )

        return results

    # ========================================================
    # WAIT BETWEEN ACTIONS
    # ========================================================

    @staticmethod
    def wait_between_actions(
        previous_action,
        next_action
    ):

        previous = str(
            previous_action.get(
                "action",
                ""
            )
        ).lower()

        next_name = str(
            next_action.get(
                "action",
                ""
            )
        ).lower()

        if previous in {
            "open_application",
            "open_website",
            "open_folder",
        }:

            if ActionExecutor.is_browser_action(
                next_name
            ):

                time.sleep(
                    0.3
                )

            else:

                time.sleep(
                    1.2
                )

            return

        if previous in {
            "browser_open",
            "google_search",
            "youtube_search",
            "google_search_interactive",
            "youtube_search_interactive",
            "browser_click",
            "browser_click_text",
            "browser_click_first_result",
            "browser_type",
            "browser_press",
            "browser_new_tab",
            "browser_back",
            "browser_forward",
            "browser_refresh",
        }:

            time.sleep(
                0.4
            )

            return

        if next_name in {
            "type_text",
            "press_key",
            "click",
            "double_click",
            "right_click",
        }:

            time.sleep(
                0.5
            )

            return

        time.sleep(
            0.2
        )

    # ========================================================
    # EXECUTE ONE ACTION
    # ========================================================

    @classmethod
    def execute_action(
        cls,
        action,
        next_action=None
    ):

        intent = str(
            action.get(
                "action",
                ""
            )
        ).lower().strip()

        target = action.get(
            "target"
        )

        text = action.get(
            "text"
        )

        key = action.get(
            "key"
        )

        x = action.get(
            "x"
        )

        y = action.get(
            "y"
        )

        # ====================================================
        # SMART CHROME START
        # ====================================================

        if (
            intent == "open_application"
            and
            str(target).lower().strip()
            in {
                "chrome",
                "google chrome",
                "browser",
                "my browser",
            }
            and
            next_action is not None
            and
            cls.is_browser_action(
                str(
                    next_action.get(
                        "action",
                        ""
                    )
                ).lower()
            )
        ):

            browser = cls.get_browser()

            return browser.open_chrome()

        # ====================================================
        # WINDOWS APPLICATIONS
        # ====================================================

        if intent == "open_application":

            return (
                WindowsTools.open_application(
                    str(target)
                )
            )

        # ====================================================
        # WINDOWS WEBSITE
        # ====================================================

        if intent == "open_website":

            return (
                WindowsTools.open_website(
                    str(target)
                )
            )

        # ====================================================
        # WINDOWS FOLDER
        # ====================================================

        if intent == "open_folder":

            return (
                WindowsTools.open_folder(
                    str(target)
                )
            )

        # ====================================================
        # SCREENSHOT
        # ====================================================

        if intent == "take_screenshot":

            return (
                WindowsTools.take_screenshot()
            )

        # ====================================================
        # SYSTEM
        # ====================================================

        if intent == "system_info":

            return (
                WindowsTools.system_info()
            )

        # ====================================================
        # VOLUME
        # ====================================================

        if intent == "increase_volume":

            return (
                WindowsTools.increase_volume()
            )

        if intent == "decrease_volume":

            return (
                WindowsTools.decrease_volume()
            )

        if intent == "mute":

            return (
                WindowsTools.mute()
            )

        if intent == "unmute":

            return (
                WindowsTools.unmute()
            )

        # ====================================================
        # LOCK
        # ====================================================

        if intent == "lock_computer":

            return (
                WindowsTools.lock_computer()
            )

        # ====================================================
        # MOUSE
        # ====================================================

        if intent == "mouse_position":

            return (
                WindowsTools.get_mouse_position()
            )

        if intent == "mouse_move":

            if x is None or y is None:

                return (
                    "Mouse coordinates are missing."
                )

            try:

                return (
                    WindowsTools.move_mouse(
                        int(x),
                        int(y)
                    )
                )

            except (
                TypeError,
                ValueError
            ):

                return (
                    "Invalid mouse coordinates."
                )

        if intent == "click":

            return (
                WindowsTools.click_mouse()
            )

        if intent == "double_click":

            return (
                WindowsTools.double_click()
            )

        if intent == "right_click":

            return (
                WindowsTools.right_click()
            )

        # ====================================================
        # SCROLL
        # ====================================================

        if intent == "scroll_up":

            return (
                WindowsTools.scroll_up()
            )

        if intent == "scroll_down":

            return (
                WindowsTools.scroll_down()
            )

        # ====================================================
        # COPY / PASTE
        # ====================================================

        if intent == "copy":

            return (
                WindowsTools.copy()
            )

        if intent == "paste":

            return (
                WindowsTools.paste()
            )

        # ====================================================
        # TYPE
        # ====================================================

        if intent == "type_text":

            if text is None:

                return (
                    "There is no text to type."
                )

            return (
                WindowsTools.type_text(
                    str(text)
                )
            )

        # ====================================================
        # PRESS KEY
        # ====================================================

        if intent == "press_key":

            if not key:

                return (
                    "Key information is missing."
                )

            return (
                WindowsTools.press_key(
                    str(key)
                )
            )

        # ====================================================
        # GET BROWSER
        # ====================================================

        browser = cls.get_browser()

        # ====================================================
        # OPEN URL
        # ====================================================

        if intent == "browser_open":

            if not target:

                return (
                    "Browser URL is missing."
                )

            return (
                browser.open_url(
                    str(target)
                )
            )

        # ====================================================
        # GOOGLE SEARCH
        # ====================================================

        if intent == "google_search":

            query = (
                text
                if text is not None
                else target
            )

            if not query:

                return (
                    "Google search text is missing."
                )

            return (
                browser.google_search(
                    str(query)
                )
            )

        # ====================================================
        # YOUTUBE SEARCH
        # ====================================================

        if intent == "youtube_search":

            query = (
                text
                if text is not None
                else target
            )

            if not query:

                return (
                    "YouTube search text is missing."
                )

            return (
                browser.youtube_search(
                    str(query)
                )
            )

        # ====================================================
        # INTERACTIVE GOOGLE SEARCH
        # ====================================================

        if intent == "google_search_interactive":

            query = (
                text
                if text is not None
                else target
            )

            if not query:

                return (
                    "Google search text is missing."
                )

            return (
                browser.google_search_interactive(
                    str(query)
                )
            )

        # ====================================================
        # INTERACTIVE YOUTUBE SEARCH
        # ====================================================

        if intent == "youtube_search_interactive":

            query = (
                text
                if text is not None
                else target
            )

            if not query:

                return (
                    "YouTube search text is missing."
                )

            return (
                browser.youtube_search_interactive(
                    str(query)
                )
            )

        # ====================================================
        # CLICK ELEMENT
        # ====================================================

        if intent == "browser_click":

            if not target:

                return (
                    "Browser selector is missing."
                )

            return (
                browser.click_element(
                    str(target)
                )
            )

        # ====================================================
        # CLICK TEXT
        # ====================================================

        if intent == "browser_click_text":

            value = (
                text
                if text is not None
                else target
            )

            if not value:

                return (
                    "Text to click is missing."
                )

            return (
                browser.click_text(
                    str(value)
                )
            )

        # ====================================================
        # CLICK FIRST RESULT
        # ====================================================

        if intent == "browser_click_first_result":

            site = str(
                target
                or "youtube"
            ).lower().strip()

            if site in [
                "youtube",
                "youtube.com",
            ]:

                return (
                    browser
                    .click_first_youtube_result()
                )

            if site in [
                "google",
                "google.com",
            ]:

                return (
                    browser
                    .click_first_google_result()
                )

            return (
                "I don't know how to open the "
                "first result on that website."
            )

        # ====================================================
        # TYPE INTO BROWSER ELEMENT
        # ====================================================

        if intent == "browser_type":

            if not target:

                return (
                    "Browser selector is missing."
                )

            if text is None:

                return (
                    "There is no text to type."
                )

            return (
                browser.type_into_element(
                    str(target),
                    str(text)
                )
            )

        # ====================================================
        # BROWSER PRESS
        # ====================================================

        if intent == "browser_press":

            if not key:

                return (
                    "Browser key is missing."
                )

            return (
                browser.press_key(
                    str(key)
                )
            )

        # ====================================================
        # READ PAGE
        # ====================================================

        if intent == "browser_read_page":

            return (
                browser.get_page_text(
                    max_length=7000
                )
            )

        # ====================================================
        # READ PAGE FOR RESULTS
        # ====================================================

        if intent == "browser_read_results":

            results = (
                browser.get_result_titles(
                    limit=10
                )
            )

            if not results:

                return (
                    "I couldn't find visible results."
                )

            return "\n".join(
                f"{index}. {title}"
                for index, title in enumerate(
                    results,
                    start=1
                )
            )

        # ====================================================
        # READ LINKS
        # ====================================================

        if intent == "browser_read_links":

            links = (
                browser.get_visible_links(
                    limit=20
                )
            )

            if not links:

                return (
                    "I couldn't find visible links."
                )

            return "\n".join(
                f"{index}. {link['text']}"
                for index, link in enumerate(
                    links,
                    start=1
                )
            )

        # ====================================================
        # PAGE TITLE
        # ====================================================

        if intent == "browser_title":

            return (
                browser.get_title()
            )

        # ====================================================
        # URL
        # ====================================================

        if intent == "browser_url":

            return (
                browser.get_url()
            )

        # ====================================================
        # BACK
        # ====================================================

        if intent == "browser_back":

            return (
                browser.back()
            )

        # ====================================================
        # FORWARD
        # ====================================================

        if intent == "browser_forward":

            return (
                browser.forward()
            )

        # ====================================================
        # REFRESH
        # ====================================================

        if intent == "browser_refresh":

            return (
                browser.refresh()
            )

        # ====================================================
        # NEW TAB
        # ====================================================

        if intent == "browser_new_tab":

            return (
                browser.new_tab()
            )

        # ====================================================
        # CLOSE TAB
        # ====================================================

        if intent == "browser_close_tab":

            return (
                browser.close_tab()
            )

        # ====================================================
        # UNKNOWN
        # ====================================================

        return (
            f"Unsupported action: {intent}"
        )

    # ========================================================
    # CLOSE BROWSER
    # ========================================================

    @classmethod
    def close_browser(cls):

        browser = getattr(
            cls._local,
            "browser",
            None
        )

        if browser:

            try:

                browser.close()

            except Exception as error:

                print(
                    f"[BROWSER] Close error: "
                    f"{error}"
                )

            finally:

                cls._local.browser = None


# ============================================================
# ============================================================
#
#   🌙 LUNA EXTENDED ACTIONS (APPENDED — NOTHING CHANGED ABOVE)
#
#   Adds 40+ new action types on top of the original
#   ActionExecutor. Unknown intents still fall through to
#   the ORIGINAL execute_action, so nothing breaks.
#
#   Optional libraries (everything degrades gracefully):
#     pip install psutil screen-brightness-control pycaw comtypes opencv-python plyer
#
# ============================================================
# ============================================================

import ctypes
import datetime
import re
import subprocess

from ctypes import cast, POINTER
from pathlib import Path

# ------------------------------------------------------------
# OPTIONAL LIBRARIES
# ------------------------------------------------------------

try:
    import psutil
    LUNA_PSUTIL_OK = True
except ImportError:
    LUNA_PSUTIL_OK = False

try:
    import screen_brightness_control as luna_sbc
    LUNA_BRIGHTNESS_OK = True
except ImportError:
    LUNA_BRIGHTNESS_OK = False

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    LUNA_PYCAW_OK = True
except ImportError:
    LUNA_PYCAW_OK = False

try:
    import cv2
    LUNA_WEBCAM_OK = True
except ImportError:
    LUNA_WEBCAM_OK = False

try:
    from plyer import notification as luna_notification
    LUNA_NOTIFY_OK = True
except ImportError:
    LUNA_NOTIFY_OK = False

# ------------------------------------------------------------
# WINDOWS VIRTUAL KEY CODES (zero dependencies)
# ------------------------------------------------------------

LUNA_VK_VOLUME_MUTE = 0xAD
LUNA_VK_VOLUME_DOWN = 0xAE
LUNA_VK_VOLUME_UP = 0xAF
LUNA_VK_MEDIA_NEXT = 0xB0
LUNA_VK_MEDIA_PREV = 0xB1
LUNA_VK_MEDIA_STOP = 0xB2
LUNA_VK_MEDIA_PLAY = 0xB3
LUNA_VK_LWIN = 0x5B
LUNA_VK_UP = 0x26
LUNA_VK_DOWN = 0x28
LUNA_VK_ALT = 0x12
LUNA_VK_D = 0x44
LUNA_VK_F4 = 0x73

LUNA_CF_UNICODETEXT = 13

LUNA_WEBCAM_DIR = (
    Path.home() / "Pictures" / "LUNA_Webcam"
)


# ============================================================
# LOW-LEVEL HELPERS
# ============================================================


def _luna_tap_key(virtual_key, presses=1):

    for _ in range(presses):

        ctypes.windll.user32.keybd_event(virtual_key, 0, 0, 0)
        ctypes.windll.user32.keybd_event(virtual_key, 0, 2, 0)
        time.sleep(0.01)


def _luna_hotkey(*virtual_keys):

    for vk in virtual_keys:

        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.03)

    for vk in reversed(virtual_keys):

        ctypes.windll.user32.keybd_event(vk, 0, 2, 0)


def _luna_number_from(action, *keys):

    for key in keys:

        value = action.get(key)

        if value is None:

            continue

        match = re.search(r"-?\d+", str(value))

        if match:

            return int(match.group())

    return None


def _luna_run_powershell(command, timeout=12):

    return subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=timeout,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def _luna_clipboard_set(text):

    ctypes.windll.user32.OpenClipboard(0)

    try:

        ctypes.windll.user32.EmptyClipboard()

        handle = ctypes.windll.kernel32.GlobalAlloc(
            0x0002,
            (len(text) + 1) * 2,
        )

        pointer = ctypes.windll.kernel32.GlobalLock(handle)

        ctypes.cdll.msvcrt.wcscpy(
            ctypes.c_wchar_p(pointer),
            text,
        )

        ctypes.windll.kernel32.GlobalUnlock(handle)

        ctypes.windll.user32.SetClipboardData(
            LUNA_CF_UNICODETEXT,
            handle,
        )

    finally:

        ctypes.windll.user32.CloseClipboard()


def _luna_clipboard_get():

    if not ctypes.windll.user32.IsClipboardFormatAvailable(
        LUNA_CF_UNICODETEXT
    ):

        return None

    ctypes.windll.user32.OpenClipboard(0)

    try:

        handle = ctypes.windll.user32.GetClipboardData(
            LUNA_CF_UNICODETEXT
        )

        if not handle:

            return None

        pointer = ctypes.windll.kernel32.GlobalLock(handle)

        if not pointer:

            return None

        text = ctypes.c_wchar_p(pointer).value

        ctypes.windll.kernel32.GlobalUnlock(handle)

        return text

    finally:

        ctypes.windll.user32.CloseClipboard()


def _luna_notify(title, message):

    if not LUNA_NOTIFY_OK:

        return False

    try:

        luna_notification.notify(
            title=str(title)[:64],
            message=str(message)[:200],
            timeout=6,
            app_name="LUNA",
        )

        return True

    except Exception:

        return False


# ============================================================
# SYSTEM READINGS
# ============================================================


def _luna_battery_text():

    if LUNA_PSUTIL_OK:

        battery = psutil.sensors_battery()

        if battery:

            percent = round(battery.percent)

            if battery.power_plugged:

                return (
                    f"The laptop is charging and is at "
                    f"{percent} percent."
                )

            left = battery.secsleft

            if (
                left
                and left > 0
                and left
                not in (
                    psutil.POWER_TIME_UNLIMITED,
                    psutil.POWER_TIME_UNKNOWN,
                )
            ):

                hours = int(left // 3600)
                minutes = int((left % 3600) // 60)

                return (
                    f"The laptop is on battery at {percent} "
                    f"percent, with about {hours} hours and "
                    f"{minutes} minutes left."
                )

            return (
                f"The laptop is on battery at "
                f"{percent} percent."
            )

    try:

        result = _luna_run_powershell(
            "(Get-CimInstance Win32_Battery)"
            ".EstimatedChargeRemaining"
        )

        value = int(
            result.stdout.strip().splitlines()[-1]
        )

        return f"The battery is at {value} percent."

    except Exception:

        return (
            "I couldn't read the battery level "
            "on this machine."
        )


def _luna_health_text():

    if LUNA_PSUTIL_OK:

        cpu = round(psutil.cpu_percent(interval=0.5))
        ram = round(psutil.virtual_memory().percent)
        disk = round(psutil.disk_usage("C:\\").percent)

        return (
            f"CPU is at {cpu} percent. "
            f"Memory is at {ram} percent. "
            f"Disk C is at {disk} percent."
        )

    try:

        result = _luna_run_powershell(
            "$cpu = (Get-CimInstance Win32_Processor | "
            "Measure-Object -Property LoadPercentage "
            "-Average).Average; "
            "$os = Get-CimInstance Win32_OperatingSystem; "
            "$ram = [math]::Round((($os.TotalVisibleMemorySize "
            "- $os.FreePhysicalMemory) / "
            "$os.TotalVisibleMemorySize) * 100); "
            "Write-Output $cpu; Write-Output $ram"
        )

        lines = [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        ]

        cpu = round(float(lines[0]))
        ram = round(float(lines[1]))

        return (
            f"CPU is at {cpu} percent. "
            f"Memory is at {ram} percent."
        )

    except Exception:

        return (
            "I couldn't read the system health "
            "on this machine."
        )


def _luna_uptime_text():

    if LUNA_PSUTIL_OK:

        seconds = int(time.time() - psutil.boot_time())

    else:

        try:

            result = _luna_run_powershell(
                "[int]((Get-Date) - (Get-CimInstance "
                "Win32_OperatingSystem).LastBootUpTime)"
                ".TotalMinutes"
            )

            seconds = int(result.stdout.strip()) * 60

        except Exception:

            return "I couldn't calculate the uptime."

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60

    parts = []

    if days:
        parts.append(f"{days} days")
    if hours:
        parts.append(f"{hours} hours")

    parts.append(f"{minutes} minutes")

    return (
        "The laptop has been on for "
        + ", ".join(parts)
        + "."
    )


# ============================================================
# VOLUME & BRIGHTNESS
# ============================================================


def _luna_volume_apply(percent):

    percent = max(0, min(100, int(percent)))

    if LUNA_PYCAW_OK:

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

        except Exception:

            pass

    # Zero-dependency fallback:
    # double-mute guarantees a muted baseline,
    # then each volume-up tap unmutes and adds 2%.

    _luna_tap_key(LUNA_VK_VOLUME_MUTE, 2)
    _luna_tap_key(
        LUNA_VK_VOLUME_UP,
        (percent + 1) // 2,
    )

    return f"Volume set to about {percent} percent."


def _luna_brightness_get():

    if LUNA_BRIGHTNESS_OK:

        try:

            level = luna_sbc.get_brightness()

            if isinstance(level, list):

                return int(level[0])

            return int(level)

        except Exception:

            pass

    try:

        result = _luna_run_powershell(
            "(Get-CimInstance -Namespace root/WMI "
            "-Class WmiMonitorBrightness).CurrentBrightness"
        )

        return int(float(result.stdout.strip()))

    except Exception:

        return None


def _luna_brightness_apply(percent):

    percent = max(0, min(100, int(percent)))

    if LUNA_BRIGHTNESS_OK:

        try:

            luna_sbc.set_brightness(percent)

            return f"Brightness set to {percent} percent."

        except Exception:

            pass

    try:

        _luna_run_powershell(
            "(Get-WmiObject -Namespace root/WMI "
            "-Class WmiMonitorBrightnessMethods)"
            f".WmiSetBrightness(1, {percent})"
        )

        return f"Brightness set to {percent} percent."

    except Exception:

        return (
            "I couldn't change the brightness "
            "on this screen."
        )


# ============================================================
# NEW ACTION HANDLERS  (cls, action, next_action) -> str
# ============================================================


def _luna_action_wait(cls, action, next_action):

    seconds = _luna_number_from(
        action,
        "seconds",
        "duration",
        "value",
    )

    if seconds is None:

        seconds = 1

    seconds = max(0, min(120, seconds))

    time.sleep(seconds)

    return f"Waited {seconds} seconds."


def _luna_action_battery(cls, action, next_action):

    return _luna_battery_text()


def _luna_action_health(cls, action, next_action):

    return _luna_health_text()


def _luna_action_uptime(cls, action, next_action):

    return _luna_uptime_text()


def _luna_action_time(cls, action, next_action):

    now = datetime.datetime.now()

    return (
        "It is "
        + now.strftime("%I:%M %p").lstrip("0")
        + "."
    )


def _luna_action_date(cls, action, next_action):

    today = datetime.date.today()

    return (
        "Today is "
        + today.strftime("%A, %B %d, %Y")
        + "."
    )


def _luna_action_screen(cls, action, next_action):

    width = ctypes.windll.user32.GetSystemMetrics(0)
    height = ctypes.windll.user32.GetSystemMetrics(1)

    return (
        f"The screen is {width} by {height} pixels."
    )


def _luna_action_wifi_status(cls, action, next_action):

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

                return (
                    f"Connected to {ssid}, "
                    f"signal strength {signal}."
                )

            return f"Connected to {ssid}."

        return "Wi-Fi is not connected."

    except Exception as error:

        return f"I couldn't check Wi-Fi: {error}"


def _luna_action_wifi_scan(cls, action, next_action):

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

        return (
            "Nearby networks: "
            + ", ".join(networks[:10])
            + "."
        )

    except Exception as error:

        return f"I couldn't scan Wi-Fi: {error}"


def _luna_action_set_volume(cls, action, next_action):

    percent = _luna_number_from(
        action,
        "percent",
        "value",
        "level",
        "amount",
        "text",
        "target",
    )

    if percent is None:

        return (
            "Tell me the volume level, "
            "for example 40 percent."
        )

    return _luna_volume_apply(percent)


def _luna_action_volume_up(cls, action, next_action):

    steps = (
        _luna_number_from(action, "steps", "amount")
        or 5
    )

    _luna_tap_key(LUNA_VK_VOLUME_UP, steps)

    return "Turning the volume up."


def _luna_action_volume_down(cls, action, next_action):

    steps = (
        _luna_number_from(action, "steps", "amount")
        or 5
    )

    _luna_tap_key(LUNA_VK_VOLUME_DOWN, steps)

    return "Turning the volume down."


def _luna_action_set_brightness(cls, action, next_action):

    percent = _luna_number_from(
        action,
        "percent",
        "value",
        "level",
        "amount",
        "text",
        "target",
    )

    if percent is None:

        return (
            "Tell me the brightness level, "
            "for example 60 percent."
        )

    return _luna_brightness_apply(percent)


def _luna_action_brightness_up(cls, action, next_action):

    level = _luna_brightness_get()

    if level is None:

        return "I couldn't read the current brightness."

    return _luna_brightness_apply(level + 10)


def _luna_action_brightness_down(cls, action, next_action):

    level = _luna_brightness_get()

    if level is None:

        return "I couldn't read the current brightness."

    return _luna_brightness_apply(level - 10)


def _luna_action_brightness_status(cls, action, next_action):

    level = _luna_brightness_get()

    if level is None:

        return (
            "I couldn't read the brightness "
            "on this screen."
        )

    return f"Brightness is at {level} percent."


def _luna_action_media_play(cls, action, next_action):

    _luna_tap_key(LUNA_VK_MEDIA_PLAY)

    return "Toggled play and pause."


def _luna_action_media_next(cls, action, next_action):

    _luna_tap_key(LUNA_VK_MEDIA_NEXT)

    return "Skipping to the next track."


def _luna_action_media_previous(cls, action, next_action):

    _luna_tap_key(LUNA_VK_MEDIA_PREV)

    return "Going to the previous track."


def _luna_action_media_stop(cls, action, next_action):

    _luna_tap_key(LUNA_VK_MEDIA_STOP)

    return "Stopping playback."


def _luna_action_sleep(cls, action, next_action):

    subprocess.Popen(
        ["rundll32.exe", "powrprof.dll,SetSuspendState 0,1,0"],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    return "Putting the laptop to sleep."


def _luna_action_restart(cls, action, next_action):

    subprocess.run(["shutdown", "/r", "/t", "5"])

    return "Restarting the laptop in 5 seconds."


def _luna_action_shutdown(cls, action, next_action):

    subprocess.run(["shutdown", "/s", "/t", "5"])

    return "Shutting down the laptop in 5 seconds."


def _luna_action_abort_shutdown(cls, action, next_action):

    try:

        subprocess.run(["shutdown", "/a"])

        return "Shutdown cancelled."

    except Exception:

        return "There is no shutdown to cancel."


def _luna_action_webcam(cls, action, next_action):

    if not LUNA_WEBCAM_OK:

        return (
            "Webcam photos need opencv. "
            "Run: pip install opencv-python"
        )

    LUNA_WEBCAM_DIR.mkdir(
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

    stamp = datetime.datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    path = LUNA_WEBCAM_DIR / f"luna_webcam_{stamp}.png"

    cv2.imwrite(str(path), frame)

    return f"Webcam photo saved to {path}."


def _luna_action_set_clipboard(cls, action, next_action):

    text = (
        action.get("text")
        or action.get("target")
    )

    if not text:

        return "There is no text to copy."

    try:

        _luna_clipboard_set(str(text))

        return "Copied to the clipboard."

    except Exception as error:

        return (
            f"I couldn't copy to the clipboard: {error}"
        )


def _luna_action_read_clipboard(cls, action, next_action):

    try:

        content = _luna_clipboard_get()

    except Exception as error:

        return f"I couldn't read the clipboard: {error}"

    if not content:

        return "The clipboard is empty."

    return f"The clipboard says: {content}"


def _luna_action_notify(cls, action, next_action):

    message = (
        action.get("text")
        or action.get("message")
        or "Reminder from LUNA."
    )

    title = action.get("title") or "LUNA"

    if _luna_notify(title, message):

        return "Notification sent."

    return f"Notification: {message}"


def _luna_action_reminder(cls, action, next_action):

    minutes = _luna_number_from(action, "minutes")
    seconds = _luna_number_from(action, "seconds")

    if minutes is None and seconds is None:

        return "Tell me how long the reminder should be."

    total = 0

    if minutes:
        total += minutes * 60
    if seconds:
        total += seconds

    if total <= 0:

        total = 60

    total = min(total, 86400)

    message = (
        action.get("text")
        or action.get("message")
        or "Your reminder is ready."
    )

    def _fire():

        time.sleep(total)

        _luna_notify("LUNA Reminder", message)

        print(f"[LUNA] ⏰ Reminder: {message}")

    threading.Thread(
        target=_fire,
        daemon=True,
    ).start()

    if total >= 60:

        return (
            f"Okay, I'll remind you in "
            f"{total // 60} minutes."
        )

    return f"Okay, I'll remind you in {total} seconds."


def _luna_action_minimize(cls, action, next_action):

    _luna_hotkey(LUNA_VK_LWIN, LUNA_VK_DOWN)
    _luna_hotkey(LUNA_VK_LWIN, LUNA_VK_DOWN)

    return "Minimized the window."


def _luna_action_maximize(cls, action, next_action):

    _luna_hotkey(LUNA_VK_LWIN, LUNA_VK_UP)

    return "Maximized the window."


def _luna_action_show_desktop(cls, action, next_action):

    _luna_hotkey(LUNA_VK_LWIN, LUNA_VK_D)

    return "Showing the desktop."


def _luna_action_switch_window(cls, action, next_action):

    _luna_hotkey(LUNA_VK_ALT, 0x09)

    return "Switched to the previous window."


def _luna_action_close_window(cls, action, next_action):

    _luna_hotkey(LUNA_VK_ALT, LUNA_VK_F4)

    return "Closed the current window."


def _luna_action_close_app(cls, action, next_action):

    target = str(
        action.get("target") or ""
    ).strip()

    if not target:

        return "Tell me which application to close."

    name = target.lower().replace(".exe", "")

    subprocess.run(
        ["taskkill", "/IM", f"{name}.exe", "/F"],
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    return f"Closed {name}."


def _luna_action_empty_bin(cls, action, next_action):

    try:

        _luna_run_powershell(
            "Clear-RecycleBin -Force "
            "-ErrorAction SilentlyContinue"
        )

        return "The recycle bin is empty."

    except Exception as error:

        return (
            f"I couldn't empty the recycle bin: {error}"
        )


# ============================================================
# BROWSER EXTRAS (reuse the thread-local browser)
# ============================================================


def _luna_page(cls):

    browser = cls.get_browser()

    if not browser.ensure_started():

        return None

    return browser.page


def _luna_action_browser_zoom_in(cls, action, next_action):

    page = _luna_page(cls)

    if page is None:

        return "Google Chrome is unavailable."

    page.keyboard.press("Control+=")

    return "Zoomed in."


def _luna_action_browser_zoom_out(cls, action, next_action):

    page = _luna_page(cls)

    if page is None:

        return "Google Chrome is unavailable."

    page.keyboard.press("Control+-")

    return "Zoomed out."


def _luna_action_browser_zoom_reset(cls, action, next_action):

    page = _luna_page(cls)

    if page is None:

        return "Google Chrome is unavailable."

    page.keyboard.press("Control+0")

    return "Reset the zoom."


def _luna_action_browser_fullscreen(cls, action, next_action):

    page = _luna_page(cls)

    if page is None:

        return "Google Chrome is unavailable."

    page.keyboard.press("F11")

    return "Toggled fullscreen."


def _luna_action_browser_find(cls, action, next_action):

    page = _luna_page(cls)

    if page is None:

        return "Google Chrome is unavailable."

    text = (
        action.get("text")
        or action.get("target")
    )

    page.keyboard.press("Control+f")

    time.sleep(0.3)

    if text:

        page.keyboard.type(
            str(text),
            delay=40,
        )

        return f"Searching the page for '{text}'."

    return "Opened the find bar."


def _luna_action_browser_scroll_top(cls, action, next_action):

    page = _luna_page(cls)

    if page is None:

        return "Google Chrome is unavailable."

    page.evaluate("window.scrollTo(0, 0)")

    return "Jumped to the top of the page."


def _luna_action_browser_scroll_bottom(cls, action, next_action):

    page = _luna_page(cls)

    if page is None:

        return "Google Chrome is unavailable."

    page.evaluate(
        "window.scrollTo(0, document.body.scrollHeight)"
    )

    return "Jumped to the bottom of the page."


def _luna_action_browser_select_all(cls, action, next_action):

    page = _luna_page(cls)

    if page is None:

        return "Google Chrome is unavailable."

    page.keyboard.press("Control+a")

    return "Selected everything on the page."


# ============================================================
# NEW INTENT REGISTRY
# ============================================================

LUNA_EXTRA_ACTIONS = {
    # --- plan flow ---
    "wait": _luna_action_wait,
    "pause": _luna_action_wait,
    # --- system readings ---
    "battery_status": _luna_action_battery,
    "check_battery": _luna_action_battery,
    "battery": _luna_action_battery,
    "system_health": _luna_action_health,
    "performance_status": _luna_action_health,
    "system_status": _luna_action_health,
    "uptime": _luna_action_uptime,
    "screen_resolution": _luna_action_screen,
    "get_time": _luna_action_time,
    "get_date": _luna_action_date,
    # --- wi-fi ---
    "wifi_status": _luna_action_wifi_status,
    "wifi_info": _luna_action_wifi_status,
    "wifi_scan": _luna_action_wifi_scan,
    "list_wifi": _luna_action_wifi_scan,
    # --- audio ---
    "set_volume": _luna_action_set_volume,
    "volume_up": _luna_action_volume_up,
    "volume_down": _luna_action_volume_down,
    # --- display ---
    "set_brightness": _luna_action_set_brightness,
    "brightness_up": _luna_action_brightness_up,
    "brightness_down": _luna_action_brightness_down,
    "brightness_status": _luna_action_brightness_status,
    # --- media keys ---
    "media_play_pause": _luna_action_media_play,
    "media_next": _luna_action_media_next,
    "media_previous": _luna_action_media_previous,
    "media_stop": _luna_action_media_stop,
    # --- power ---
    "sleep_computer": _luna_action_sleep,
    "hibernate": _luna_action_sleep,
    "restart_computer": _luna_action_restart,
    "reboot_computer": _luna_action_restart,
    "shutdown_computer": _luna_action_shutdown,
    "abort_shutdown": _luna_action_abort_shutdown,
    # --- capture & clipboard ---
    "take_webcam_photo": _luna_action_webcam,
    "set_clipboard": _luna_action_set_clipboard,
    "read_clipboard": _luna_action_read_clipboard,
    # --- desktop experience ---
    "show_notification": _luna_action_notify,
    "set_reminder": _luna_action_reminder,
    "minimize_window": _luna_action_minimize,
    "maximize_window": _luna_action_maximize,
    "show_desktop": _luna_action_show_desktop,
    "switch_window": _luna_action_switch_window,
    "close_window": _luna_action_close_window,
    "close_application": _luna_action_close_app,
    "empty_recycle_bin": _luna_action_empty_bin,
    # --- browser extras ---
    "browser_zoom_in": _luna_action_browser_zoom_in,
    "browser_zoom_out": _luna_action_browser_zoom_out,
    "browser_zoom_reset": _luna_action_browser_zoom_reset,
    "browser_fullscreen": _luna_action_browser_fullscreen,
    "browser_find": _luna_action_browser_find,
    "browser_scroll_top": _luna_action_browser_scroll_top,
    "browser_scroll_bottom": _luna_action_browser_scroll_bottom,
    "browser_select_all": _luna_action_browser_select_all,
}

LUNA_BROWSER_EXTRA_NAMES = {
    "browser_zoom_in",
    "browser_zoom_out",
    "browser_zoom_reset",
    "browser_fullscreen",
    "browser_find",
    "browser_scroll_top",
    "browser_scroll_bottom",
    "browser_select_all",
}

LUNA_ORIGINAL_ACTIONS = {
    "open_application", "open_website", "open_folder",
    "take_screenshot", "system_info",
    "increase_volume", "decrease_volume", "mute", "unmute",
    "lock_computer",
    "mouse_position", "mouse_move", "click", "double_click",
    "right_click", "scroll_up", "scroll_down",
    "copy", "paste", "type_text", "press_key",
    "browser_open", "google_search", "youtube_search",
    "google_search_interactive", "youtube_search_interactive",
    "browser_click", "browser_click_text",
    "browser_click_first_result", "browser_type",
    "browser_press", "browser_read_page",
    "browser_read_results", "browser_read_links",
    "browser_title", "browser_url", "browser_back",
    "browser_forward", "browser_refresh",
    "browser_new_tab", "browser_close_tab",
}


# ============================================================
# HOOK THE NEW ACTIONS INTO ACTIONEXECUTOR
# (original execute_action is preserved and used as fallback)
# ============================================================

_original_execute_action = (
    ActionExecutor.execute_action.__func__
)

_original_is_browser_action = (
    ActionExecutor.is_browser_action
)

_original_wait_between_actions = (
    ActionExecutor.wait_between_actions
)


def _extended_execute_action(cls, action, next_action=None):

    intent = ""

    if isinstance(action, dict):

        intent = str(
            action.get("action", "")
        ).lower().strip()

    handler = LUNA_EXTRA_ACTIONS.get(intent)

    if handler:

        return handler(cls, action, next_action)

    return _original_execute_action(
        cls,
        action,
        next_action,
    )


def _extended_is_browser_action(action_name):

    if action_name in LUNA_BROWSER_EXTRA_NAMES:

        return True

    return _original_is_browser_action(action_name)


def _extended_wait_between_actions(previous_action, next_action):

    previous = str(
        previous_action.get("action", "")
    ).lower()

    if previous in LUNA_BROWSER_EXTRA_NAMES:

        time.sleep(0.4)

        return

    if previous == "wait":

        return

    return _original_wait_between_actions(
        previous_action,
        next_action,
    )


ActionExecutor.execute_action = classmethod(
    _extended_execute_action
)

ActionExecutor.is_browser_action = staticmethod(
    _extended_is_browser_action
)

ActionExecutor.wait_between_actions = staticmethod(
    _extended_wait_between_actions
)


def _list_supported_actions(cls):

    return sorted(
        LUNA_ORIGINAL_ACTIONS
        | set(LUNA_EXTRA_ACTIONS)
    )


ActionExecutor.list_actions = classmethod(
    _list_supported_actions
)

print(
    f"[LUNA] Extended actions loaded: "
    f"{len(LUNA_EXTRA_ACTIONS)} new action types."
)