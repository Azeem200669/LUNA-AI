from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QSizePolicy,
)


class MessageBubble(QFrame):

    def __init__(
        self,
        sender: str,
        message: str,
        is_user: bool = False,
        parent=None,
    ):
        super().__init__(parent)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Minimum,
        )

        self.setObjectName(
            "UserMessageFrame"
            if is_user
            else "LunaMessageFrame"
        )

        self.setStyleSheet(
            """
            QFrame#UserMessageFrame {
                background: #081824;
                border: 1px solid #0c5064;
                border-radius: 15px;
            }

            QFrame#LunaMessageFrame {
                background: #07131d;
                border: 1px solid #173443;
                border-radius: 15px;
            }
            """
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            14,
            11,
            14,
            11,
        )

        layout.setSpacing(5)

        sender_label = QLabel(
            sender.upper()
        )

        sender_label.setStyleSheet(
            """
            color: #00e5ff;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 2px;
            background: transparent;
            border: none;
            """
        )

        message_label = QLabel(
            message
        )

        message_label.setWordWrap(
            True
        )

        message_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        message_label.setStyleSheet(
            """
            color: #dffaff;
            font-size: 13px;
            background: transparent;
            border: none;
            """
        )

        layout.addWidget(
            sender_label
        )

        layout.addWidget(
            message_label
        )


class ChatPanel(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.thinking_label = None

        self.setup_ui()

    def setup_ui(self):

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(
            8
        )

        # ----------------------------------------------
        # TITLE
        # ----------------------------------------------

        title = QLabel(
            "C O N V E R S A T I O N"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet(
            """
            color: #e8fbff;
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 6px;
            background: transparent;
            """
        )

        main_layout.addWidget(
            title
        )

        # ----------------------------------------------
        # SUBTITLE
        # ----------------------------------------------

        subtitle = QLabel(
            "Your conversation with LUNA"
        )

        subtitle.setAlignment(
            Qt.AlignCenter
        )

        subtitle.setStyleSheet(
            """
            color: #35596c;
            font-size: 11px;
            background: transparent;
            """
        )

        main_layout.addWidget(
            subtitle
        )

        # ----------------------------------------------
        # SMALL LINE
        # ----------------------------------------------

        divider_container = QVBoxLayout()

        divider_container.setContentsMargins(
            0,
            4,
            0,
            4,
        )

        divider = QFrame()

        divider.setFixedSize(
            48,
            2,
        )

        divider.setStyleSheet(
            """
            background: #123847;
            border-radius: 1px;
            """
        )

        divider_container.addWidget(
            divider,
            alignment=Qt.AlignCenter,
        )

        main_layout.addLayout(
            divider_container
        )

        # ----------------------------------------------
        # SCROLL
        # ----------------------------------------------

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(
            True
        )

        self.scroll.setFrameShape(
            QFrame.NoFrame
        )

        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }

            QScrollBar:vertical {
                width: 5px;
                background: transparent;
                margin: 2px;
            }

            QScrollBar::handle:vertical {
                background: #123b4a;
                border-radius: 2px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background: #00bdd8;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )

        # ----------------------------------------------
        # CONTAINER
        # ----------------------------------------------

        self.container = QWidget()

        self.messages = QVBoxLayout(
            self.container
        )

        self.messages.setContentsMargins(
            5,
            8,
            5,
            8,
        )

        self.messages.setSpacing(
            12
        )

        self.messages.addStretch()

        self.scroll.setWidget(
            self.container
        )

        main_layout.addWidget(
            self.scroll,
            1,
        )

        # ----------------------------------------------
        # FOOTER
        # ----------------------------------------------

        footer = QLabel(
            "Conversation history"
        )

        footer.setStyleSheet(
            """
            color: #35596c;
            font-size: 11px;
            background: transparent;
            """
        )

        main_layout.addWidget(
            footer
        )

    # ==================================================
    # ADD USER
    # ==================================================

    def add_user_message(
        self,
        message: str,
    ):

        self._add_message(
            "You",
            message,
            True,
        )

    # ==================================================
    # ADD LUNA
    # ==================================================

    def add_luna_message(
        self,
        message: str,
    ):

        self._add_message(
            "LUNA",
            message,
            False,
        )

    # ==================================================
    # GENERIC
    # ==================================================

    def _add_message(
        self,
        sender: str,
        message: str,
        is_user: bool,
    ):

        bubble = MessageBubble(
            sender,
            message,
            is_user,
        )

        self.messages.insertWidget(
            self.messages.count() - 1,
            bubble,
        )

        self.scroll_to_bottom()

    # ==================================================
    # THINKING
    # ==================================================

    def show_thinking(self):

        if self.thinking_label is not None:
            return

        self.thinking_label = QLabel(
            "LUNA  •  thinking..."
        )

        self.thinking_label.setStyleSheet(
            """
            color: #00dff5;
            font-size: 11px;
            font-style: italic;
            padding: 7px;
            background: transparent;
            """
        )

        self.messages.insertWidget(
            self.messages.count() - 1,
            self.thinking_label,
        )

        self.scroll_to_bottom()

    # ==================================================
    # HIDE THINKING
    # ==================================================

    def hide_thinking(self):

        if self.thinking_label is None:
            return

        self.thinking_label.deleteLater()

        self.thinking_label = None

    # ==================================================
    # CLEAR
    # ==================================================

    def clear_messages(self):

        self.hide_thinking()

        while self.messages.count() > 1:

            item = self.messages.takeAt(0)

            widget = item.widget()

            if widget:
                widget.deleteLater()

    # ==================================================
    # SCROLL
    # ==================================================

    def scroll_to_bottom(self):

        bar = self.scroll.verticalScrollBar()

        bar.setValue(
            bar.maximum()
        )


# ============================================================
# ============================================================
#
#   🌙 LUNA CHAT PANEL PRO — EXTENSIONS (APPEND ONLY)
#
#   The original MessageBubble and ChatPanel above are
#   100% unchanged. The Pro versions below subclass them
#   and add:
#
#     • Timestamps on every bubble
#     • Smooth fade-in animation for new bubbles
#     • Right-click any bubble → "Copy message"
#     • Animated typing indicator (pulsing dots)
#     • Smart auto-scroll — if you scrolled up to
#       re-read, LUNA won't yank you back down
#     • Floating "↓ Latest" jump-to-bottom button
#     • Status lines: add_status_message / add_action_result
#     • Streaming: stream_to_luna() appends text to the
#       last LUNA bubble token-by-token
#     • get_conversation(), export_conversation(),
#       copy_conversation(), message_count()
#
#   Drop-in: the aliases at the bottom make every import
#   of MessageBubble / ChatPanel resolve to the Pro versions.
#
# ============================================================
# ============================================================

import datetime
from pathlib import Path

from PySide6.QtCore import (
    Qt,
    QAbstractAnimation,
    QEasingCurve,
    QPropertyAnimation,
    QTimer,
)
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QMenu,
    QPushButton,
)


# ============================================================
# ANIMATED TYPING INDICATOR
# ============================================================


class ThinkingIndicator(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            7,
            0,
            7,
            0,
        )

        layout.setSpacing(2)

        self.text_label = QLabel(
            "LUNA is thinking"
        )

        self.text_label.setStyleSheet(
            """
            color: #00dff5;
            font-size: 11px;
            font-style: italic;
            background: transparent;
            """
        )

        self.dots_label = QLabel("")

        self.dots_label.setStyleSheet(
            """
            color: #00dff5;
            font-size: 11px;
            font-style: italic;
            background: transparent;
            """
        )

        layout.addWidget(
            self.text_label
        )

        layout.addWidget(
            self.dots_label
        )

        layout.addStretch()

        self._phase = 0

        self._timer = QTimer(self)

        self._timer.timeout.connect(
            self._tick
        )

        self._timer.start(280)

    def _tick(self):

        self._phase = (
            (self._phase + 1) % 4
        )

        self.dots_label.setText(
            "•" * self._phase
        )

    def showEvent(self, event):

        self._timer.start(280)

        super().showEvent(event)

    def hideEvent(self, event):

        self._timer.stop()

        super().hideEvent(event)


# ============================================================
# MESSAGE BUBBLE PRO
# ============================================================


class MessageBubblePro(MessageBubble):

    def __init__(
        self,
        sender: str,
        message: str,
        is_user: bool = False,
        parent=None,
        show_timestamp: bool = True,
    ):
        super().__init__(
            sender,
            message,
            is_user,
            parent,
        )

        # -----------------------------
        # RECOVER BASE WIDGETS
        # (the base stores them locally,
        #  so pull them from the layout)
        # -----------------------------

        base_layout = self.layout()

        self.sender_label = (
            base_layout.itemAt(0).widget()
        )

        self.message_label = (
            base_layout.itemAt(1).widget()
        )

        # -----------------------------
        # DATA
        # -----------------------------

        self.is_user = bool(is_user)

        self.sender_name = str(sender)

        self.message_text = str(message)

        self.timestamp_text = (
            datetime.datetime.now()
            .strftime("%H:%M")
        )

        # -----------------------------
        # TIMESTAMP HEADER
        # -----------------------------

        self.time_label = QLabel(
            self.timestamp_text
        )

        self.time_label.setStyleSheet(
            """
            color: #3c5c68;
            font-size: 9px;
            font-weight: 600;
            background: transparent;
            border: none;
            """
        )

        base_layout.removeWidget(
            self.sender_label
        )

        header = QHBoxLayout()

        header.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        header.setSpacing(8)

        header.addWidget(
            self.sender_label
        )

        if show_timestamp:

            header.addStretch()

            header.addWidget(
                self.time_label
            )

        base_layout.insertLayout(
            0,
            header,
        )

        # -----------------------------
        # RIGHT-CLICK COPY
        # -----------------------------

        self.setContextMenuPolicy(
            Qt.CustomContextMenu
        )

        self.customContextMenuRequested.connect(
            self._show_context_menu
        )

    # ------------------------------------------------
    # TEXT UPDATES (used by streaming)
    # ------------------------------------------------

    def set_text(self, text):

        self.message_text = str(text)

        self.message_label.setText(
            self.message_text
        )

    def append_text(self, chunk):

        self.message_text += str(chunk)

        self.message_label.setText(
            self.message_text
        )

    # ------------------------------------------------
    # DATA
    # ------------------------------------------------

    def get_data(self):

        return {
            "sender": self.sender_name,
            "text": self.message_text,
            "time": self.timestamp_text,
            "is_user": self.is_user,
        }

    # ------------------------------------------------
    # CONTEXT MENU
    # ------------------------------------------------

    def _show_context_menu(self, position):

        menu = QMenu(self)

        copy_action = menu.addAction(
            "Copy message"
        )

        chosen = menu.exec(
            self.mapToGlobal(position)
        )

        if chosen == copy_action:

            QApplication.clipboard().setText(
                self.message_text
            )


# ============================================================
# CHAT PANEL PRO
# ============================================================


class ChatPanelPro(ChatPanel):

    TONE_COLORS = {
        "info": "#5b8fa8",
        "success": "#5aff96",
        "error": "#ff6b81",
        "alert": "#ffa046",
    }

    def __init__(self, parent=None):

        super().__init__(parent)

        # -----------------------------
        # SCROLL STATE
        # -----------------------------

        self._stick_to_bottom = True

        # -----------------------------
        # STREAMING
        # -----------------------------

        self._last_luna_bubble = None

        # -----------------------------
        # EFFECTS
        # -----------------------------

        self.animations_enabled = True

        # -----------------------------
        # JUMP-TO-LATEST BUTTON
        # -----------------------------

        self._build_jump_button()

        bar = self.scroll.verticalScrollBar()

        bar.valueChanged.connect(
            self._on_scroll_moved
        )

        bar.rangeChanged.connect(
            self._on_range_changed
        )

    # ==================================================
    # MESSAGE INSERTION (fade + smart scroll)
    # ==================================================

    def _add_message(
        self,
        sender: str,
        message: str,
        is_user: bool,
    ):

        bubble = MessageBubblePro(
            sender,
            message,
            is_user,
        )

        self._insert_bubble(bubble)

        if not is_user:

            self._last_luna_bubble = bubble

    def _insert_bubble(self, widget):

        was_stuck = self._stick_to_bottom

        self._apply_fade(widget)

        self.messages.insertWidget(
            self.messages.count() - 1,
            widget,
        )

        if was_stuck:

            self.scroll_to_bottom()

        else:

            self.jump_button.show()

            self._position_jump_button()

    def _apply_fade(self, widget):

        if not self.animations_enabled:

            return

        effect = QGraphicsOpacityEffect(
            widget
        )

        effect.setOpacity(0.0)

        widget.setGraphicsEffect(effect)

        animation = QPropertyAnimation(
            effect,
            b"opacity",
            widget,
        )

        animation.setDuration(200)

        animation.setStartValue(0.0)

        animation.setEndValue(1.0)

        animation.setEasingCurve(
            QEasingCurve.OutCubic
        )

        animation.finished.connect(
            lambda w=widget: w.setGraphicsEffect(None)
        )

        animation.start(
            QAbstractAnimation.DeleteWhenStopped
        )

    # ==================================================
    # THINKING (animated override)
    # ==================================================

    def show_thinking(self):

        if self.thinking_label is not None:
            return

        self.thinking_label = (
            ThinkingIndicator()
        )

        self._apply_fade(
            self.thinking_label
        )

        self.messages.insertWidget(
            self.messages.count() - 1,
            self.thinking_label,
        )

        if self._stick_to_bottom:

            self.scroll_to_bottom()

    # ==================================================
    # CLEAR (reset overrides)
    # ==================================================

    def clear_messages(self):

        super().clear_messages()

        self._last_luna_bubble = None

        self._stick_to_bottom = True

        self.jump_button.hide()

    # ==================================================
    # SMART SCROLL + JUMP BUTTON
    # ==================================================

    def _build_jump_button(self):

        self.jump_button = QPushButton(
            "↓  Latest",
            self,
        )

        self.jump_button.setCursor(
            Qt.PointingHandCursor
        )

        self.jump_button.setStyleSheet(
            """
            QPushButton {
                background: #071923;
                color: #00eaff;
                border: 1px solid #194351;
                border-radius: 12px;
                padding: 5px 12px;
                font-size: 11px;
                font-weight: 700;
            }

            QPushButton:hover {
                background: #0c2530;
                border: 1px solid #00eaff;
            }
            """
        )

        self.jump_button.hide()

        self.jump_button.raise_()

        self.jump_button.clicked.connect(
            self._jump_to_latest
        )

    def _position_jump_button(self):

        if not self.jump_button.isVisible():

            return

        self.jump_button.adjustSize()

        x = (
            self.width()
            - self.jump_button.width()
            - 18
        )

        y = (
            self.height()
            - self.jump_button.height()
            - 44
        )

        self.jump_button.move(
            x,
            y,
        )

    def _jump_to_latest(self):

        self._stick_to_bottom = True

        self.scroll_to_bottom()

        self.jump_button.hide()

    def _on_scroll_moved(self, value):

        bar = self.scroll.verticalScrollBar()

        at_bottom = (
            value
            >= bar.maximum() - 60
        )

        self._stick_to_bottom = at_bottom

        if at_bottom:

            self.jump_button.hide()

        elif self.jump_button.isHidden():

            self.jump_button.show()

            self._position_jump_button()

    def _on_range_changed(self, minimum, maximum):

        if self._stick_to_bottom:

            self.scroll.verticalScrollBar().setValue(
                maximum
            )

        self._position_jump_button()

    def resizeEvent(self, event):

        super().resizeEvent(event)

        self._position_jump_button()

    # ==================================================
    # STATUS / ACTION RESULT LINES
    # ==================================================

    def add_status_message(
        self,
        text,
        tone="info",
    ):

        color = self.TONE_COLORS.get(
            tone,
            self.TONE_COLORS["info"],
        )

        label = QLabel(
            f"●  {text}"
        )

        label.setAlignment(
            Qt.AlignCenter
        )

        label.setWordWrap(
            True
        )

        label.setStyleSheet(
            f"""
            color: {color};
            font-size: 11px;
            font-style: italic;
            padding: 4px;
            background: transparent;
            """
        )

        self._insert_bubble(label)

        return label

    def add_action_result(self, result_text):

        text = str(result_text)

        lowered = text.lower()

        if any(
            word in lowered
            for word in (
                "couldn",
                "error",
                "failed",
                "unsupported",
            )
        ):

            tone = "error"

        else:

            tone = "success"

        return self.add_status_message(
            text,
            tone,
        )

    # ==================================================
    # STREAMING
    # ==================================================

    def stream_to_luna(self, chunk):

        if not chunk:

            return

        bubble = self._last_luna_bubble

        if bubble is None:

            self.add_luna_message(
                str(chunk)
            )

            return

        try:

            bubble.append_text(str(chunk))

        except RuntimeError:

            self._last_luna_bubble = None

            self.add_luna_message(str(chunk))

            return

        if self._stick_to_bottom:

            self.scroll_to_bottom()

    def update_last_luna_message(self, text):

        bubble = self._last_luna_bubble

        if bubble is None:

            return

        try:

            bubble.set_text(str(text))

        except RuntimeError:

            self._last_luna_bubble = None

    def finish_stream(self):

        self._last_luna_bubble = None

    # ==================================================
    # HISTORY / EXPORT
    # ==================================================

    def get_conversation(self):

        items = []

        for index in range(
            self.messages.count()
        ):

            widget = (
                self.messages
                .itemAt(index)
                .widget()
            )

            if widget is None:

                continue

            get_data = getattr(
                widget,
                "get_data",
                None,
            )

            if callable(get_data):

                items.append(
                    get_data()
                )

        return items

    def conversation_as_text(self):

        lines = []

        for item in self.get_conversation():

            lines.append(
                f"[{item['time']}] "
                f"{item['sender']}: "
                f"{item['text']}"
            )

        return "\n".join(lines)

    def export_conversation(self, path=None):

        text = self.conversation_as_text()

        if not text:

            return (
                "There is no conversation "
                "to export."
            )

        if path is None:

            folder = (
                Path.home()
                / "LUNA_Conversations"
            )

            folder.mkdir(
                parents=True,
                exist_ok=True,
            )

            path = (
                folder
                / (
                    "luna_chat_"
                    + datetime.datetime.now()
                    .strftime("%Y%m%d_%H%M%S")
                    + ".txt"
                )
            )

        Path(path).write_text(
            text,
            encoding="utf-8",
        )

        return f"Conversation saved to {path}."

    def copy_conversation(self):

        text = self.conversation_as_text()

        if not text:

            return (
                "There is no conversation "
                "to copy."
            )

        QApplication.clipboard().setText(text)

        return (
            f"Copied "
            f"{len(self.get_conversation())} "
            f"messages to the clipboard."
        )

    def message_count(self):

        return len(
            self.get_conversation()
        )


# ------------------------------------------------------------
# DROP-IN UPGRADE
# MessageBubble and ChatPanel now resolve to the Pro
# versions everywhere (same API, more features).
# Delete these two lines to keep the originals.
# ------------------------------------------------------------

MessageBubble = MessageBubblePro

ChatPanel = ChatPanelPro


# ============================================================
# QUICK TEST (uncomment to preview)
# ============================================================
#
# if __name__ == "__main__":
#
#     import sys
#     from PySide6.QtWidgets import QApplication
#
#     app = QApplication(sys.argv)
#
#     panel = ChatPanel()
#     panel.resize(420, 640)
#     panel.show()
#
#     panel.add_user_message("Hey LUNA!")
#     panel.add_luna_message("Hello! I'm ready when you are.")
#     panel.add_status_message("Screenshot saved.", "success")
#     panel.add_status_message("Wi-Fi check failed.", "error")
#     panel.show_thinking()
#
#     sys.exit(app.exec())