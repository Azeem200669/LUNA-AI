import sys

from PySide6.QtWidgets import QApplication

from ui.window import LunaWindow


def main():

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "LUNA"
    )

    app.setApplicationDisplayName(
        "LUNA - Personal AI Assistant"
    )

    window = LunaWindow()

    window.show()

    sys.exit(
        app.exec()
    )


# ============================================================
# ============================================================
#
#   🌙 LUNA LAUNCHER PRO — INSERTED SECTION (ADD-ONLY)
#
#   Nothing above was changed. This section sits before the
#   runner line so the ORIGINAL `if __name__ == "__main__":`
#   below stays byte-identical and now boots Pro.
#
#   Adds:
#     • 🛡️  Crash guard — errors logged + friendly dialog
#     • 📜  Session logs — console tee'd to ~/LUNA_Logs/
#     • 🔒  Single-instance lock (no double mic/audio fights)
#     • 🖥️  High-DPI crisp rendering
#     • 🎨  Fusion + dark palette safety net for native dialogs
#     • 🌅  Painted splash screen (zero assets)
#     • 🖼️  App icon painted in code (taskbar/titlebar)
#     • 🚩  Flags: --classic --demo --no-splash --fresh
#                  --wake-word --no-log
#     • 💥  Previous-crash notice at boot
#     • ⌨️  Clean Ctrl+C shutdown
#
# ============================================================
# ============================================================

import os
import math
import traceback
import datetime

from pathlib import Path

from PySide6.QtCore import (
    Qt,
    QPointF,
    QLockFile,
)

from PySide6.QtGui import (
    QIcon,
    QFont,
    QPixmap,
    QPainter,
    QColor,
    QPen,
    QBrush,
    QRadialGradient,
    QPalette,
    QPolygonF,
)

from PySide6.QtWidgets import (
    QApplication,
    QSplashScreen,
    QMessageBox,
)


LUNA_VERSION = "1.0.0"

LUNA_LOG_DIR = (
    Path.home() / "LUNA_Logs"
)

LUNA_CRASH_FLAG = (
    LUNA_LOG_DIR / "last_crash.txt"
)

LUNA_LOCK_PATH = (
    Path(
        os.environ.get(
            "LOCALAPPDATA",
            str(Path.home()),
        )
    )
    / "LUNA"
    / "luna.lock"
)


# ============================================================
# SESSION LOG (console tee)
# ============================================================

_LUNA_LOG_FILE = None

_LUNA_LOG_PATH = None

_LUNA_STDOUT_ORIG = None

_LUNA_STDERR_ORIG = None


class _LunaSessionTee:

    def __init__(
        self,
        original,
        log_file,
    ):

        self._original = original

        self._log = log_file

    def write(self, text):

        try:

            self._original.write(text)

            self._original.flush()

        except Exception:

            pass

        try:

            self._log.write(text)

            self._log.flush()

        except Exception:

            pass

        return len(text)

    def flush(self):

        try:

            self._original.flush()

        except Exception:

            pass

        try:

            self._log.flush()

        except Exception:

            pass

    def isatty(self):

        try:

            return self._original.isatty()

        except Exception:

            return False

    def __getattr__(self, name):

        return getattr(
            self._original,
            name,
        )


def _start_session_log(flags):

    global _LUNA_LOG_FILE
    global _LUNA_LOG_PATH
    global _LUNA_STDOUT_ORIG
    global _LUNA_STDERR_ORIG

    if "--no-log" in flags:

        return

    try:

        LUNA_LOG_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        stamp = (datetime.datetime.now()
        .strftime("%Y%m%d_%H%M%S"))

        _LUNA_LOG_PATH = (
            LUNA_LOG_DIR
            / f"luna_session_{stamp}.log"
        )

        _LUNA_LOG_FILE = open(
            _LUNA_LOG_PATH,
            "a",
            encoding="utf-8",
        )

        _LUNA_STDOUT_ORIG = sys.stdout

        _LUNA_STDERR_ORIG = sys.stderr

        sys.stdout = _LunaSessionTee(
            sys.stdout,
            _LUNA_LOG_FILE,
        )

        sys.stderr = _LunaSessionTee(
            sys.stderr,
            _LUNA_LOG_FILE,
        )

    except Exception as error:

        print(
            f"[LUNA] Session log disabled: {error}"
        )


def _stop_session_log():

    global _LUNA_LOG_FILE
    global _LUNA_STDOUT_ORIG
    global _LUNA_STDERR_ORIG

    if _LUNA_STDOUT_ORIG is not None:

        sys.stdout = _LUNA_STDOUT_ORIG

        _LUNA_STDOUT_ORIG = None

    if _LUNA_STDERR_ORIG is not None:

        sys.stderr = _LUNA_STDERR_ORIG

        _LUNA_STDERR_ORIG = None

    if _LUNA_LOG_FILE is not None:

        try:

            _LUNA_LOG_FILE.close()

        except Exception:

            pass

        _LUNA_LOG_FILE = None


# ============================================================
# CRASH GUARD
# ============================================================


def _install_crash_guard():

    previous_hook = sys.excepthook

    def _hook(
        error_type,
        error_value,
        error_trace,
    ):

        details = "".join(
            traceback.format_exception(
                error_type,
                error_value,
                error_trace,
            )
        )

        try:

            LUNA_LOG_DIR.mkdir(
                parents=True,
                exist_ok=True,
            )

            LUNA_CRASH_FLAG.write_text(
                details,
                encoding="utf-8",
            )

        except Exception:

            pass

        print(
            "💥 LUNA crashed — details saved to "
            f"{LUNA_CRASH_FLAG}"
        )

        if QApplication.instance():

            try:

                box = QMessageBox()

                box.setIcon(
                    QMessageBox.Critical
                )

                box.setWindowTitle(
                    "LUNA"
                )

                box.setText(
                    "LUNA hit an unexpected "
                    "error and had to stop."
                )

                box.setInformativeText(
                    f"Details were saved to:\n"
                    f"{LUNA_CRASH_FLAG}"
                )

                box.setDetailedText(
                    details
                )

                box.exec()

            except Exception:

                pass

        if previous_hook:

            previous_hook(
                error_type,
                error_value,
                error_trace,
            )

    sys.excepthook = _hook


def _note_previous_crash():

    try:

        if not LUNA_CRASH_FLAG.exists():

            return

        lines = (
            LUNA_CRASH_FLAG
            .read_text(
                encoding="utf-8",
                errors="ignore",
            )
            .strip()
            .splitlines()
        )

        summary = (
            lines[-1]
            if lines
            else "unknown error"
        )

        print(
            "⚠️  Previous session ended "
            f"unexpectedly: {summary}"
        )

        print(
            f"    Full details: "
            f"{LUNA_CRASH_FLAG}"
        )

        LUNA_CRASH_FLAG.unlink()

    except Exception:

        pass


# ============================================================
# SINGLE INSTANCE
# ============================================================

_LUNA_LOCK = None


def _acquire_single_instance():

    global _LUNA_LOCK

    try:

        LUNA_LOCK_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    except Exception:

        pass

    lock = QLockFile(
        str(LUNA_LOCK_PATH)
    )

    if not lock.tryLock(0):

        print(
            "🔒 LUNA is already running."
        )

        try:

            import ctypes

            ctypes.windll.user32.MessageBoxW(
                0,
                "LUNA is already running.",
                "LUNA",
                0x40,
            )

        except Exception:

            pass

        return False

    _LUNA_LOCK = lock

    return True


def _release_single_instance():

    global _LUNA_LOCK

    if _LUNA_LOCK is None:

        return

    try:

        _LUNA_LOCK.unlock()

    except Exception:

        pass

    _LUNA_LOCK = None


# ============================================================
# PAINTED BADGE / ICON / SPLASH (zero assets)
# ============================================================


def _paint_luna_badge(size):

    pixmap = QPixmap(size, size)

    pixmap.fill(QColor("#02070D"))

    painter = QPainter(pixmap)

    painter.setRenderHint(
        QPainter.Antialiasing,
        True,
    )

    c = size / 2

    glow = QRadialGradient(
        c,
        c,
        size * 0.45,
    )

    glow.setColorAt(
        0.0,
        QColor(0, 235, 255, 190),
    )

    glow.setColorAt(
        0.4,
        QColor(0, 140, 220, 80),
    )

    glow.setColorAt(
        1.0,
        QColor(0, 60, 120, 0),
    )

    painter.setPen(Qt.NoPen)

    painter.setBrush(QBrush(glow))

    painter.drawEllipse(
        0,
        0,
        size,
        size,
    )

    for radius, alpha, width in [

        (0.46, 200, 5),
        (0.36, 150, 3),
        (0.27, 110, 2),

    ]:

        r = size * radius

        pen = QPen(
            QColor(0, 230, 255, alpha)
        )

        pen.setWidthF(width)

        painter.setPen(pen)

        painter.setBrush(Qt.NoBrush)

        painter.drawEllipse(
            int(c - r),
            int(c - r),
            int(r * 2),
            int(r * 2),
        )

    painter.setPen(Qt.NoPen)

    painter.setBrush(
        QColor(255, 255, 255, 245)
    )

    star = size * 0.11

    points = []

    for i in range(8):

        angle = (
            -math.pi / 2
            + i * math.pi / 4
        )

        r = (
            star
            if i % 2 == 0
            else star * 0.3
        )

        points.append(
            QPointF(
                c + math.cos(angle) * r,
                c + math.sin(angle) * r,
            )
        )

    painter.drawPolygon(
        QPolygonF(points)
    )

    painter.end()

    return pixmap


def _make_splash():

    size = 460

    pixmap = QPixmap(size, size)

    pixmap.fill(QColor("#02070D"))

    badge = _paint_luna_badge(
        int(size * 0.78)
    )

    painter = QPainter(pixmap)

    painter.setRenderHint(
        QPainter.Antialiasing,
        True,
    )

    painter.drawPixmap(
        int(size * 0.11),
        int(size * 0.02),
        badge,
    )

    font = QFont("Segoe UI")

    font.setPixelSize(40)

    font.setBold(True)

    font.setLetterSpacing(
        QFont.AbsoluteSpacing,
        10,
    )

    painter.setFont(font)

    painter.setPen(
        QColor(245, 255, 255)
    )

    painter.drawText(
        0,
        int(size * 0.72),
        size,
        60,
        Qt.AlignHCenter,
        "L U N A",
    )

    font.setPixelSize(14)

    font.setBold(False)

    font.setLetterSpacing(
        QFont.AbsoluteSpacing,
        3,
    )

    painter.setFont(font)

    painter.setPen(
        QColor(72, 104, 120)
    )

    painter.drawText(
        0,
        int(size * 0.80),
        size,
        30,
        Qt.AlignHCenter,
        "PERSONAL AI ASSISTANT",
    )

    painter.end()

    splash = QSplashScreen(pixmap)

    splash.showMessage(
        "waking up...",
        Qt.AlignBottom | Qt.AlignHCenter,
        QColor(0, 234, 255),
    )

    return splash


# ============================================================
# DARK PALETTE SAFETY NET
# (native dialogs, menus, message boxes match the theme)
# ============================================================


def _apply_dark_palette(app):

    palette = QPalette()

    palette.setColor(
        QPalette.Window,
        QColor("#0a1017"),
    )

    palette.setColor(
        QPalette.WindowText,
        QColor("#e8fbff"),
    )

    palette.setColor(
        QPalette.Base,
        QColor("#050b12"),
    )

    palette.setColor(
        QPalette.AlternateBase,
        QColor("#0a141f"),
    )

    palette.setColor(
        QPalette.Text,
        QColor("#e8fbff"),
    )

    palette.setColor(
        QPalette.Button,
        QColor("#07111a"),
    )

    palette.setColor(
        QPalette.ButtonText,
        QColor("#e8fbff"),
    )

    palette.setColor(
        QPalette.ToolTipBase,
        QColor("#0c2530"),
    )

    palette.setColor(
        QPalette.ToolTipText,
        QColor("#baf3ff"),
    )

    palette.setColor(
        QPalette.Highlight,
        QColor("#00cfe8"),
    )

    palette.setColor(
        QPalette.HighlightedText,
        QColor("#031017"),
    )

    palette.setColor(
        QPalette.PlaceholderText,
        QColor("#56717f"),
    )

    palette.setColor(
        QPalette.Disabled,
        QPalette.Text,
        QColor("#3c5c68"),
    )

    palette.setColor(
        QPalette.Disabled,
        QPalette.WindowText,
        QColor("#3c5c68"),
    )

    palette.setColor(
        QPalette.Disabled,
        QPalette.ButtonText,
        QColor("#3c5c68"),
    )

    app.setPalette(palette)


# ============================================================
# BANNER
# ============================================================


def _print_banner():

    print()

    print("=" * 48)

    print(
        f"  🌙 LUNA v{LUNA_VERSION} · "
        f"{datetime.datetime.now():%Y-%m-%d %H:%M}"
    )

    print(
        f"  Python {sys.version.split()[0]}"
    )

    if _LUNA_LOG_PATH:

        print(f"  Log: {_LUNA_LOG_PATH}")

    print("=" * 48)

    print()

    print(
        "  Flags: --classic --demo --no-splash "
        "--fresh --wake-word --no-log"
    )

    print()


# ============================================================
# ENHANCED LAUNCHER
# ============================================================


def luna():

    flags = {
        argument.lower()
        for argument in sys.argv[1:]
    }

    # ----------------------------------------------
    # CLASSIC — your original main, untouched
    # ----------------------------------------------

    if "--classic" in flags:

        print(
            "[LUNA] Classic launch "
            "(original main)."
        )

        return _classic_main()

    # ----------------------------------------------
    # PRO LAUNCH SEQUENCE
    # ----------------------------------------------

    _install_crash_guard()

    _start_session_log(flags)

    _print_banner()

    _note_previous_crash()

    if (
        "--fresh" not in flags
        and not _acquire_single_instance()
    ):

        _stop_session_log()

        return 1

    # Must be set BEFORE QApplication exists

    (QApplication
    .setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy
        .PassThrough
    ))

    app = QApplication(sys.argv)

    app.setApplicationName("LUNA")

    app.setApplicationDisplayName(
        "LUNA - Personal AI Assistant"
    )

    app.setStyle("Fusion")

    app.setWindowIcon(
        QIcon(_paint_luna_badge(256))
    )

    _apply_dark_palette(app)

    # ----------------------------------------------
    # SPLASH (visible during heavy init)
    # ----------------------------------------------

    splash = None

    if "--no-splash" not in flags:

        splash = _make_splash()

        splash.show()

        app.processEvents()

        splash.showMessage(
            "loading your assistant...",
            Qt.AlignBottom | Qt.AlignHCenter,
            QColor(0, 234, 255),
        )

        app.processEvents()

    # ----------------------------------------------
    # WINDOW (heavy init happens here)
    # ----------------------------------------------

    window = LunaWindow()

    # ----------------------------------------------
    # FLAG-DRIVEN HOOKS
    # ----------------------------------------------

    if "--wake-word" in flags:

        if hasattr(
            window,
            "set_voice_idle_timeout",
        ):

            window.set_voice_idle_timeout(
                300
            )

        if hasattr(
            window,
            "set_wake_word_required",
        ):

            window.set_wake_word_required(
                True
            )

    window.show()

    if splash:

        splash.finish(window)

    # ----------------------------------------------
    # WELCOME TOUCHES
    # ----------------------------------------------

    if hasattr(
        window.core,
        "show_message",
    ):

        window.core.show_message(
            "LUNA is ready ✨",
            3.0,
        )

    if hasattr(
        window.conversation,
        "add_status_message",
    ):

        (window.conversation
        .add_status_message(
            "Session started — say hello!",
            "info",
        ))

    if (
        "--demo" in flags
        and hasattr(window.core, "start_demo")
    ):

        window.core.start_demo()

    # ----------------------------------------------
    # RUN
    # ----------------------------------------------

    exit_code = 0

    try:

        exit_code = app.exec()

    except KeyboardInterrupt:

        print(
            "\n[LUNA] Interrupted — "
            "shutting down gracefully."
        )

        exit_code = 0

    finally:

        _release_single_instance()

        _stop_session_log()

    return exit_code


# ------------------------------------------------------------
# ENTRY REBIND (the alias-equivalent for an entry file)
# The original main is preserved as _classic_main;
# the name `main` now boots the enhanced launcher.
# ------------------------------------------------------------

_classic_main = main


def main():

    sys.exit(
        luna()
    )


# ============================================================
# ORIGINAL RUNNER — UNTOUCHED
# ============================================================

if __name__ == "__main__":
    main()