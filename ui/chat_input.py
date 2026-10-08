from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
)


class ChatInput(QWidget):

    send_requested = Signal(str)

    microphone_requested = Signal()

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setup_ui()

    # ==================================================
    # UI
    # ==================================================

    def setup_ui(self):

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(8)

        # ----------------------------------------------
        # INPUT
        # ----------------------------------------------

        self.input = QLineEdit()

        self.input.setPlaceholderText(
            "Type a command or ask LUNA..."
        )

        self.input.setMinimumHeight(58)

        self.input.returnPressed.connect(
            self.send
        )

        layout.addWidget(
            self.input,
            1,
        )

        # ----------------------------------------------
        # MICROPHONE
        # ----------------------------------------------

        self.mic_button = QPushButton(
            "🎙"
        )

        self.mic_button.setObjectName(
            "VoiceButton"
        )

        self.mic_button.setFixedSize(
            58,
            58,
        )

        self.mic_button.clicked.connect(
            self.microphone_requested.emit
        )

        layout.addWidget(
            self.mic_button
        )

        # ----------------------------------------------
        # SEND
        # ----------------------------------------------

        self.send_button = QPushButton(
            "Send"
        )

        self.send_button.setObjectName(
            "SendButton"
        )

        self.send_button.setFixedSize(
            108,
            58,
        )

        self.send_button.clicked.connect(
            self.send
        )

        layout.addWidget(
            self.send_button
        )

    # ==================================================
    # SEND
    # ==================================================

    def send(self):

        text = self.input.text().strip()

        if not text:
            return

        self.input.clear()

        self.send_requested.emit(
            text
        )

    # ==================================================
    # ENABLE/DISABLE
    # ==================================================

    def set_enabled(
        self,
        enabled: bool,
    ):

        self.input.setEnabled(
            enabled
        )

        self.send_button.setEnabled(
            enabled
        )

        self.mic_button.setEnabled(
            enabled
        )

    # ==================================================
    # FOCUS
    # ==================================================

    def focus_input(self):

        self.input.setFocus()


# ============================================================
# ============================================================
#
#   🌙 LUNA CHAT INPUT PRO — EXTENSIONS (APPEND ONLY)
#
#   The original ChatInput above is 100% unchanged.
#   ChatInputPro subclasses it and adds:
#
#     • Quick action chips (📸 🔋 💻 📶 📺) — one-tap commands
#     • Command history (↑ / ↓ like a terminal, draft kept)
#     • Escape clears the input + escape_pressed signal
#     • Busy mode — Send becomes a red Stop button
#     • Listening mode — mic button turns green
#     • Rotating placeholder hints while idle
#     • typing_changed signal ("user started/stopped typing")
#     • chip_clicked signal for analytics / custom handling
#
#   Uses the object names from the STYLE sheet:
#     QPushButton#Chip, QPushButton#DangerButton,
#     VoiceButton[active="true"]
#
# ============================================================
# ============================================================

from PySide6.QtCore import (
    Qt,
    QEvent,
    QTimer,
    Signal,
)


def _chat_repolish(widget):

    widget.style().unpolish(widget)

    widget.style().polish(widget)


class ChatInputPro(ChatInput):

    # ==================================================
    # SIGNALS
    # ==================================================

    stop_requested = Signal()

    escape_pressed = Signal()

    typing_changed = Signal(bool)

    chip_clicked = Signal(str)

    # ==================================================
    # HINTS (first hint = the original placeholder,
    # so the first idle cycle looks identical)
    # ==================================================

    DEFAULT_HINTS = [
        "Type a command or ask LUNA...",
        "Try: what's my battery level",
        "Try: take a screenshot",
        "Try: system health",
        "Try: open youtube",
        "Try: set volume to 40",
        "Try: remind me in 10 minutes",
    ]

    # ==================================================
    # DEFAULT CHIPS  (emoji, command, tooltip)
    # ==================================================

    DEFAULT_CHIPS = [
        ("📸", "take a screenshot", "Take a screenshot"),
        ("🔋", "what's my battery level", "Battery status"),
        ("💻", "system health", "CPU / RAM / disk"),
        ("📶", "wi-fi status", "Wi-Fi status"),
        ("📺", "open youtube", "Open YouTube"),
    ]

    def __init__(self, parent=None):

        super().__init__(parent)

        # -----------------------------
        # STATE
        # -----------------------------

        self._enabled = True

        self._busy = False

        self._listening = False

        self._was_typing = False

        # -----------------------------
        # HISTORY
        # -----------------------------

        self._history = []

        self._history_index = 0

        self._history_draft = ""

        # -----------------------------
        # HINT ROTATION
        # -----------------------------

        self._hints = list(
            self.DEFAULT_HINTS
        )

        self._hint_index = 0

        self._hints_enabled = True

        self._hint_timer = QTimer(self)

        self._hint_timer.timeout.connect(
            self._rotate_hint
        )

        self._hint_timer.start(6000)

        # -----------------------------
        # BUILD EXTRAS
        # -----------------------------

        self._chip_buttons = []

        self._build_chips()

        # -----------------------------
        # HOOKS
        # (original wiring is untouched —
        #  these connect IN ADDITION)
        # -----------------------------

        self.input.installEventFilter(
            self
        )

        self.send_button.clicked.connect(
            self._handle_send_click
        )

        self.send_requested.connect(
            self._record_history
        )

        self.input.textChanged.connect(
            self._handle_text_changed
        )

    # ==================================================
    # QUICK ACTION CHIPS
    # ==================================================

    def _build_chips(self):

        self.chips_bar = QWidget(self)

        chips_layout = QHBoxLayout(
            self.chips_bar
        )

        chips_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        chips_layout.setSpacing(5)

        for (
            emoji,
            command,
            tooltip
        ) in self.DEFAULT_CHIPS:

            self.add_chip(
                emoji,
                command,
                tooltip,
            )

        # insert BEFORE the input field
        # (original layout is not modified)

        self.layout().insertWidget(
            0,
            self.chips_bar,
        )

    def add_chip(
        self,
        emoji,
        command,
        tooltip="",
    ):

        chip = QPushButton(
            str(emoji)
        )

        chip.setObjectName(
            "Chip"
        )

        chip.setFixedSize(
            38,
            38,
        )

        chip.setToolTip(
            tooltip or command
        )

        chip.setCursor(
            Qt.PointingHandCursor
        )

        chip.clicked.connect(
            lambda checked=False,
            c=str(command): self._on_chip(c)
        )

        self._chip_buttons.append(
            chip
        )

        self.chips_bar.layout().addWidget(
            chip
        )

        if self._busy:

            chip.setEnabled(False)

        return chip

    def clear_chips(self):

        for chip in self._chip_buttons:

            chip.setParent(None)

            chip.deleteLater()

        self._chip_buttons = []

    def set_chips_visible(self, visible):

        self.chips_bar.setVisible(
            bool(visible)
        )

    def _on_chip(self, command):

        self.chip_clicked.emit(
            command
        )

        # flows through the SAME path as
        # typed text, so the app needs no
        # extra wiring to handle chips

        self.send_requested.emit(
            command
        )

    # ==================================================
    # COMMAND HISTORY (↑ / ↓)
    # ==================================================

    def _record_history(self, text):

        text = str(text).strip()

        if not text:

            return

        if (
            self._history
            and self._history[-1] == text
        ):

            self._history_index = (
                len(self._history)
            )

            return

        self._history.append(text)

        if len(self._history) > 100:

            self._history.pop(0)

        self._history_index = (
            len(self._history)
        )

    def _history_back(self):

        if not self._history:

            return

        if (
            self._history_index
            >= len(self._history)
        ):

            self._history_draft = (
                self.input.text()
            )

        if self._history_index > 0:

            self._history_index -= 1

        text = self._history[
            self._history_index
        ]

        self.input.setText(text)

        self.input.setCursorPosition(
            len(text)
        )

    def _history_forward(self):

        if (
            self._history_index
            >= len(self._history)
        ):

            return

        self._history_index += 1

        if (
            self._history_index
            >= len(self._history)
        ):

            self.input.setText(
                self._history_draft
            )

            self._history_draft = ""

        else:

            text = self._history[
                self._history_index
            ]

            self.input.setText(text)

            self.input.setCursorPosition(
                len(text)
            )

    def get_history(self):

        return list(self._history)

    def clear_history(self):

        self._history = []

        self._history_index = 0

        self._history_draft = ""

    def load_history(self, items):

        cleaned = [
            str(item)
            for item in items
            if str(item).strip()
        ]

        self._history = cleaned[-100:]

        self._history_index = (
            len(self._history)
        )

    # ==================================================
    # BUSY MODE — Send becomes Stop
    # ==================================================

    def set_busy(self, busy):

        busy = bool(busy)

        if busy == self._busy:

            return

        self._busy = busy

        self.input.setEnabled(
            self._enabled and not busy
        )

        self.mic_button.setEnabled(
            self._enabled and not busy
        )

        self.send_button.setEnabled(
            self._enabled
        )

        for chip in self._chip_buttons:

            chip.setEnabled(
                self._enabled and not busy
            )

        if busy:

            self.send_button.setText(
                "Stop"
            )

            self.send_button.setObjectName(
                "DangerButton"
            )

            self.input.setPlaceholderText(
                "LUNA is working... "
                "click Stop to cancel"
            )

        else:

            self.send_button.setText(
                "Send"
            )

            self.send_button.setObjectName(
                "SendButton"
            )

            self._hint_index = 0

            self.input.setPlaceholderText(
                self._hints[0]
            )

            if (
                self._enabled
                and self.isVisible()
            ):

                self.input.setFocus()

        _chat_repolish(
            self.send_button
        )

    def is_busy(self):

        return self._busy

    def _handle_send_click(self):

        # When busy, the original send()
        # is a no-op (input is empty and
        # disabled) — so this turns the
        # same button into a Stop button.

        if self._busy:

            self.stop_requested.emit()

    # ==================================================
    # LISTENING MODE — green mic
    # ==================================================

    def set_listening(self, active):

        self._listening = bool(active)

        self.mic_button.setProperty(
            "active",
            self._listening,
        )

        _chat_repolish(
            self.mic_button
        )

    set_recording = set_listening

    def is_listening(self):

        return self._listening

    # ==================================================
    # ENABLE/DISABLE (busy-aware override)
    # ==================================================

    def set_enabled(
        self,
        enabled: bool,
    ):

        self._enabled = bool(enabled)

        if self._busy:

            self.input.setEnabled(False)

            self.mic_button.setEnabled(False)

            self.send_button.setEnabled(
                self._enabled
            )

        else:

            super().set_enabled(enabled)

        for chip in self._chip_buttons:

            chip.setEnabled(
                self._enabled
                and not self._busy
            )

    # ==================================================
    # PLACEHOLDER HINTS
    # ==================================================

    def _rotate_hint(self):

        if not self._hints_enabled:

            return

        if self._busy:

            return

        if self.input.text():

            return

        self.input.setPlaceholderText(
            self._hints[
                self._hint_index
                % len(self._hints)
            ]
        )

        self._hint_index += 1

    def set_hints(self, hints):

        cleaned = [
            str(hint)
            for hint in hints
            if str(hint)
        ]

        if not cleaned:

            return

        self._hints = cleaned

        self._hint_index = 0

        if (
            not self._busy
            and not self.input.text()
        ):

            self.input.setPlaceholderText(
                self._hints[0]
            )

    def set_hints_enabled(self, enabled):

        self._hints_enabled = bool(
            enabled
        )

        if enabled:

            self._hint_timer.start(6000)

        else:

            self._hint_timer.stop()

    def set_placeholder(self, text):

        # custom placeholder — stop the
        # rotation so it stays visible

        self._hints_enabled = False

        self._hint_timer.stop()

        self.input.setPlaceholderText(
            str(text)
        )

    # ==================================================
    # TYPING DETECTION
    # ==================================================

    def _handle_text_changed(self, text):

        typing = bool(
            str(text).strip()
        )

        if typing != self._was_typing:

            self._was_typing = typing

            self.typing_changed.emit(
                typing
            )

    # ==================================================
    # KEY HANDLING — ↑ ↓ ESC
    # ==================================================

    def eventFilter(self, obj, event):

        if (
            obj is self.input
            and event.type() == QEvent.KeyPress
        ):

            key = event.key()

            if key == Qt.Key_Up:

                self._history_back()

                return True

            if key == Qt.Key_Down:

                self._history_forward()

                return True

            if key == Qt.Key_Escape:

                if self.input.text():

                    self.input.clear()

                self.escape_pressed.emit()

                return True

        return super().eventFilter(
            obj,
            event
        )

    # ==================================================
    # SMALL EXTRAS
    # ==================================================

    def clear_input(self):

        self.input.clear()


# ------------------------------------------------------------
# DROP-IN UPGRADE
# Anything that imports ChatInput from this file now gets the
# extended version automatically (same API, more features).
# Delete the next line to keep using the original input row.
# ------------------------------------------------------------

ChatInput = ChatInputPro


# ============================================================
# QUICK TEST (uncomment to try the new features)
# ============================================================
#
# if __name__ == "__main__":
#
#     import sys
#     from PySide6.QtWidgets import QApplication
#
#     app = QApplication(sys.argv)
#
#     widget = ChatInput()
#     widget.show()
#
#     # try:
#     #   ↑ / ↓      → history recall
#     #   Esc        → clear input
#     #   chips      → one-tap commands
#     #   widget.set_busy(True)   → Send turns into red Stop
#     #   widget.set_listening(True) → mic turns green
#
#     sys.exit(app.exec())