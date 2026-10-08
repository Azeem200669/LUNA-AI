from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
)

from PySide6.QtCore import (
    Qt,
    QThread,
    Signal,
)

import threading

from ui.styles import STYLE
from ui.luna_core import LunaCore
from ui.chat_panel import ChatPanel
from ui.chat_input import ChatInput
from ui.voice_worker import VoiceWorker

from core.agent import LunaAgent
from core.action_executor import ActionExecutor
from voice.text_to_speech import TextToSpeech
from core.stop_control import GenerationGuard


# ============================================================
# AI WORKER
# ============================================================

class AIWorker(QThread):

    finished = Signal(str)
    error = Signal(str)

    def __init__(
        self,
        agent,
        message,
        request_id=0,
        generation=0,
    ):

        super().__init__()

        self.agent = agent
        self.message = message
        self.request_id = request_id
        self.generation = generation
        self._cancelled = threading.Event()

    def cancel(self):
        """Request cancellation without force-killing the Python thread."""
        self._cancelled.set()
        self.requestInterruption()

    @property
    def cancelled(self):
        return self._cancelled.is_set() or self.isInterruptionRequested()

    def run(self):

        try:

            if self.cancelled:
                self.finished.emit("")
                return

            response = self.agent.chat(
                self.message,
                model="groq"
            )

            # The provider call may already be in progress when cancel()
            # is requested. Never deliver a stale response after STOP.
            if self.cancelled:
                self.finished.emit("")
                return

            self.finished.emit(
                response or ""
            )

        except Exception as error:

            if self.cancelled:
                return

            self.error.emit(
                str(error)
            )


# ============================================================
# TTS WORKER
# ============================================================

class TTSWorker(QThread):

    finished = Signal()
    error = Signal(str)

    def __init__(
        self,
        text,
    ):

        super().__init__()

        self.text = text
        self.generation = 0
        self._cancelled = threading.Event()
        self.tts = None

    def stop(self):
        """Stop speech immediately and prevent any late completion."""
        self._cancelled.set()
        self.requestInterruption()

        tts = self.tts
        if tts is not None:
            try:
                tts.stop()
            except Exception:
                pass

        # TextToSpeech uses pygame's global music stream. Stopping it here
        # gives the GUI an immediate hard stop even during playback.
        try:
            import pygame
            pygame.mixer.music.stop()
        except Exception:
            pass

    def run(self):

        try:

            if self._cancelled.is_set():
                return

            self.tts = TextToSpeech()

            if self._cancelled.is_set():
                self.tts.stop()
                return

            self.tts.speak(
                self.text
            )

            if self._cancelled.is_set():
                return

            self.finished.emit()

        except Exception as error:

            if not self._cancelled.is_set():
                self.error.emit(
                    str(error)
                )

        finally:
            self.tts = None


# ============================================================
# LUNA WINDOW
# ============================================================

class LunaWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        # ----------------------------------------------------
        # WINDOW
        # ----------------------------------------------------

        self.setWindowTitle(
            "LUNA - Personal AI Assistant"
        )

        self.resize(
            1450,
            900
        )

        self.setMinimumSize(
            1100,
            700
        )

        self.setStyleSheet(
            STYLE
        )

        # ----------------------------------------------------
        # LUNA COMPONENTS
        # ----------------------------------------------------

        self.agent = LunaAgent()

        self.ai_worker = None

        self.tts_worker = None

        self.voice_worker = None

        # Phase 13: generation/cancellation guard. A stopped request must
        # never deliver a late answer into the UI or restart TTS.
        self._request_counter = 0
        self._active_request_id = 0
        self._generation_guard = GenerationGuard()
        self._active_tts_generation = 0

        # ----------------------------------------------------
        # BUILD UI
        # ----------------------------------------------------

        self.build_ui()

    # ========================================================
    # BUILD UI
    # ========================================================

    def build_ui(self):

        central = QWidget()

        self.setCentralWidget(
            central
        )

        root = QVBoxLayout(
            central
        )

        root.setContentsMargins(
            35,
            25,
            35,
            25
        )

        root.setSpacing(
            12
        )

        # ====================================================
        # HEADER
        # ====================================================

        header = QHBoxLayout()

        title_area = QVBoxLayout()

        title = QLabel(
            "LUNA"
        )

        title.setObjectName(
            "Title"
        )

        subtitle = QLabel(
            "Personal AI Assistant"
        )

        subtitle.setObjectName(
            "Subtitle"
        )

        title_area.addWidget(
            title
        )

        title_area.addWidget(
            subtitle
        )

        header.addLayout(
            title_area
        )

        header.addStretch()

        self.status = QLabel(
            "● ONLINE"
        )

        self.status.setObjectName(
            "Status"
        )

        header.addWidget(
            self.status,
            alignment=Qt.AlignTop
        )

        root.addLayout(
            header
        )

        # ====================================================
        # MAIN BODY
        # ====================================================

        body = QHBoxLayout()

        body.setSpacing(
            25
        )

        # ====================================================
        # LEFT SIDE
        # ====================================================

        left = QWidget()

        left_layout = QVBoxLayout(
            left
        )

        left_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        # ----------------------------------------------------
        # HOLOGRAPHIC CORE
        # ----------------------------------------------------

        self.core = LunaCore()

        left_layout.addWidget(
            self.core,
            1
        )

        # ----------------------------------------------------
        # INPUT AREA
        # ----------------------------------------------------

        input_frame = QFrame()

        input_frame.setObjectName(
            "InputFrame"
        )

        input_layout = QHBoxLayout(
            input_frame
        )

        input_layout.setContentsMargins(
            8,
            8,
            8,
            8
        )

        self.chat_input = ChatInput()

        input_layout.addWidget(
            self.chat_input
        )

        left_layout.addWidget(
            input_frame
        )

        # ====================================================
        # RIGHT SIDE - CONVERSATION
        # ====================================================

        conversation_frame = QFrame()

        conversation_frame.setObjectName(
            "MessagePanel"
        )

        conversation_frame.setFixedWidth(
            385
        )

        conversation_layout = QVBoxLayout(
            conversation_frame
        )

        conversation_layout.setContentsMargins(
            18,
            18,
            18,
            18
        )

        self.conversation = ChatPanel()

        conversation_layout.addWidget(
            self.conversation
        )

        # ====================================================
        # ADD TO BODY
        # ====================================================

        body.addWidget(
            left,
            1
        )

        body.addWidget(
            conversation_frame
        )

        root.addLayout(
            body,
            1
        )

        # ====================================================
        # CONNECT UI SIGNALS
        # ====================================================

        self.chat_input.send_requested.connect(
            self.handle_text
        )

        self.chat_input.microphone_requested.connect(
            self.toggle_voice
        )

    # ========================================================
    # HANDLE MANUAL TEXT
    # ========================================================

    def handle_text(
        self,
        message,
    ):

        message = str(
            message
        ).strip()

        if not message:
            return

        # ----------------------------------------------------
        # Global STOP command
        # ----------------------------------------------------

        command = message.lower().strip().rstrip("?.!")

        if command in {
            "stop",
            "stop luna",
            "stop speaking",
            "cancel",
            "cancel luna",
        }:
            self.stop_all("text-command")
            return

        # ----------------------------------------------------
        # Don't start duplicate requests
        # ----------------------------------------------------

        if self.ai_worker is not None:

            print(
                "[LUNA] AI request already running."
            )

            return

        if self.voice_worker is not None:

            print(
                "[LUNA] Voice mode is active."
            )

            return

        print()
        print(
            f"👤 You: {message}"
        )

        # ----------------------------------------------------
        # SHOW USER MESSAGE
        # ----------------------------------------------------

        self.conversation.add_user_message(
            message
        )

        # ----------------------------------------------------
        # THINKING
        # ----------------------------------------------------

        self.conversation.show_thinking()

        self.set_state(
            "thinking"
        )

        # ----------------------------------------------------
        # DISABLE TEXT INPUT
        # ----------------------------------------------------

        self.chat_input.set_enabled(
            False
        )

        # ----------------------------------------------------
        # START AI THREAD
        # ----------------------------------------------------

        generation = self._generation_guard.next()
        self._request_counter += 1
        self._active_request_id = self._request_counter

        self.ai_worker = AIWorker(
            self.agent,
            message,
            request_id=self._active_request_id,
            generation=generation,
        )

        self.ai_worker.finished.connect(
            self.ai_finished
        )

        self.ai_worker.error.connect(
            self.ai_error
        )

        self.ai_worker.start()

    # ========================================================
    # AI RESPONSE
    # ========================================================

    def ai_finished(
        self,
        response,
    ):

        worker = self.sender()
        if not isinstance(worker, AIWorker):
            worker = self.ai_worker

        if worker is None:
            return

        # Ignore a late signal from an older/cancelled request.
        if worker.request_id != self._active_request_id:
            return
        if not self._generation_guard.is_current(worker.generation):
            return

        self.conversation.hide_thinking()

        if worker.cancelled:
            self.ai_worker = None
            self.set_state("idle")
            self.enable_input()
            self.chat_input.mic_button.setText("🎙")
            self.chat_input.mic_button.setEnabled(True)
            return

        if not response:
            response = "I didn't receive a response."

        response = str(response).strip()
        if not response:
            return

        print(f"🌙 LUNA: {response}")
        self.conversation.add_luna_message(response)

        # Start a TTS worker tied to the same generation.
        tts_generation = self._generation_guard.current()
        self._active_tts_generation = tts_generation

        self.set_state("speaking")
        self.tts_worker = TTSWorker(response)
        self.tts_worker.generation = tts_generation

        self.tts_worker.finished.connect(
            lambda gen=tts_generation: self.tts_finished(gen)
        )
        self.tts_worker.error.connect(
            lambda error, gen=tts_generation: self.tts_error(error, gen)
        )
        self.tts_worker.start()

        self.chat_input.mic_button.setEnabled(True)
        self.chat_input.mic_button.setText("🛑")
        self.ai_worker = None

    # ========================================================
    # AI ERROR
    # ========================================================

    def ai_error(
        self,
        error,
    ):

        worker = self.sender()
        if isinstance(worker, AIWorker):
            if worker.request_id != self._active_request_id:
                return
            if not self._generation_guard.is_current(worker.generation):
                return
            if worker.cancelled:
                return

        print(f"❌ AI error: {error}")
        self.conversation.hide_thinking()
        self.conversation.add_luna_message(
            "I'm unable to reach my AI service right now."
        )
        self.ai_worker = None
        self.set_state("idle")
        self.enable_input()

    # ========================================================
    # TTS FINISHED
    # ========================================================

    def tts_finished(self, generation=0):

        worker = self.tts_worker
        if worker is None:
            return

        if generation and generation != self._active_tts_generation:
            return

        if not self._generation_guard.is_current(generation or self._active_tts_generation):
            return

        self.tts_worker = None
        self._active_tts_generation = 0
        self.set_state("idle")
        self.enable_input()
        self.chat_input.mic_button.setText("🎙")
        self.chat_input.mic_button.setEnabled(True)

    # ========================================================
    # TTS ERROR
    # ========================================================

    def tts_error(self, error, generation=0):

        if generation and generation != self._active_tts_generation:
            return

        if not self._generation_guard.is_current(generation or self._active_tts_generation):
            return

        print(f"❌ TTS error: {error}")
        self.tts_worker = None
        self._active_tts_generation = 0
        self.set_state("idle")
        self.enable_input()
        self.chat_input.mic_button.setText("🎙")
        self.chat_input.mic_button.setEnabled(True)

    # ========================================================
    # ENABLE INPUT
    # ========================================================

    def enable_input(self):

        self.chat_input.set_enabled(
            True
        )

        self.chat_input.focus_input()

    # ========================================================
    # VOICE / GLOBAL STOP TOGGLE
    # ========================================================

    def toggle_voice(self):

        # During AI/TTS activity the mic button becomes a global STOP
        # control instead of starting another voice session.
        if self.ai_worker is not None or self.tts_worker is not None:
            self.stop_all("button")
            return

        if self.voice_worker is not None:
            self.stop_voice()
        else:
            self.start_voice()

    # ========================================================
    # GLOBAL STOP
    # ========================================================

    def stop_all(self, reason="user"):
        """Stop audio/voice immediately and suppress stale AI output."""
        self._generation_guard.invalidate()

        stopped = False

        self._active_tts_generation = 0

        if self.tts_worker is not None:
            print("[LUNA] STOP: stopping text-to-speech...")
            try:
                self.tts_worker.stop()
            except Exception:
                pass
            stopped = True

        if self.voice_worker is not None:
            print("[LUNA] STOP: stopping voice worker...")
            try:
                self.voice_worker.stop()
            except Exception:
                pass
            stopped = True

        if self.ai_worker is not None:
            print("[LUNA] STOP: cancelling current AI request...")
            try:
                self.ai_worker.cancel()
            except Exception:
                pass
            stopped = True

        # Global pygame stop is cheap and makes the button/ESC path
        # immediate even if the worker is between two TTS operations.
        try:
            import pygame
            pygame.mixer.music.stop()
        except Exception:
            pass

        self.conversation.hide_thinking()
        self.set_state("idle")

        if self.voice_worker is None:
            self.chat_input.mic_button.setText("🎙")
            self.chat_input.mic_button.setEnabled(True)

        # Text can be accepted immediately only when no AI thread remains.
        # We avoid starting a new request concurrently with an in-flight
        # provider call because QThread cancellation is cooperative.
        if self.ai_worker is None:
            self.enable_input()
        else:
            self.chat_input.input.setEnabled(False)
            self.chat_input.send_button.setEnabled(False)

        if stopped:
            print(f"[LUNA] STOP completed ({reason}).")
        else:
            print("[LUNA] Nothing active to stop.")

    def keyPressEvent(self, event):
        """ESC is an emergency local STOP control."""
        if event.key() == Qt.Key_Escape:
            self.stop_all("escape")
            event.accept()
            return

        super().keyPressEvent(event)

    # ========================================================
    # START VOICE
    # ========================================================

    def start_voice(self):

        if self.voice_worker is not None:
            return

        if self.ai_worker is not None:

            print(
                "[LUNA] Please wait for the current request."
            )

            return

        print(
            "\n🎙️ Starting LUNA voice mode..."
        )

        # -----------------------------------------------
        # Disable typing while voice mode is active
        # -----------------------------------------------

        self.chat_input.input.setEnabled(
            False
        )

        self.chat_input.send_button.setEnabled(
            False
        )

        # Keep microphone button active
        # so it can stop voice mode.

        self.chat_input.mic_button.setEnabled(
            True
        )

        # -----------------------------------------------
        # Worker
        # -----------------------------------------------

        self.voice_worker = VoiceWorker()

        self.voice_worker.state_changed.connect(
            self.set_state
        )

        self.voice_worker.user_text.connect(
            self.voice_user_message
        )

        self.voice_worker.luna_response.connect(
            self.voice_luna_message
        )

        self.voice_worker.error.connect(
            self.voice_error
        )

        self.voice_worker.finished.connect(
            self.voice_finished
        )

        # -----------------------------------------------
        # Start
        # -----------------------------------------------

        self.voice_worker.start()

        self.chat_input.mic_button.setText(
            "🛑"
        )

    # ========================================================
    # STOP VOICE
    # ========================================================

    def stop_voice(self):

        if self.voice_worker is None:
            return

        print(
            "\n🛑 Stopping LUNA voice mode..."
        )

        self.voice_worker.stop()

        try:
            import pygame
            pygame.mixer.music.stop()
        except Exception:
            pass

        self.chat_input.mic_button.setText(
            "🎙"
        )
        self.chat_input.mic_button.setEnabled(True)

        self.set_state(
            "idle"
        )

    # ========================================================
    # VOICE USER MESSAGE
    # ========================================================

    def voice_user_message(
        self,
        text
    ):

        self.conversation.add_user_message(
            text
        )

    # ========================================================
    # VOICE LUNA MESSAGE
    # ========================================================

    def voice_luna_message(
        self,
        response
    ):

        self.conversation.add_luna_message(
            response
        )

    # ========================================================
    # VOICE ERROR
    # ========================================================

    def voice_error(
        self,
        error
    ):

        print(
            f"❌ Voice error: {error}"
        )

    # ========================================================
    # VOICE FINISHED
    # ========================================================

    def voice_finished(self):

        self.voice_worker = None

        self.chat_input.mic_button.setText(
            "🎙"
        )

        self.set_state(
            "idle"
        )

        if self.ai_worker is None and self.tts_worker is None:
            self.chat_input.set_enabled(True)
            self.chat_input.focus_input()

        self.chat_input.mic_button.setText("🎙")
        self.chat_input.mic_button.setEnabled(True)

    # ========================================================
    # CHANGE LUNA STATE
    # ========================================================

    def set_state(
        self,
        state,
    ):

        state = str(
            state
        ).lower()

        self.core.set_state(
            state
        )

        status_text = {

            "idle":
                "● ONLINE",

            "listening":
                "● LISTENING",

            "thinking":
                "● THINKING",

            "speaking":
                "● SPEAKING",
        }

        self.status.setText(
            status_text.get(
                state,
                "● ONLINE"
            )
        )

    # ========================================================
    # CLOSE WINDOW
    # ========================================================

    def closeEvent(
        self,
        event,
    ):

        print(
            "\n🌙 Closing LUNA..."
        )

        self.stop_all("window-close")

        if self.voice_worker:
            self.voice_worker.wait(1500)

        if self.ai_worker:
            self.ai_worker.wait(1500)

        if self.tts_worker:
            self.tts_worker.wait(1500)

        try:
            self.agent.shutdown()
        except Exception as error:
            print(f"[LUNA] Agent shutdown warning: {error}")

        event.accept()


# ============================================================
# ============================================================
#
#   🌙 LUNA WINDOW PRO — ORCHESTRATION EXTENSIONS (APPEND ONLY)
#
#   The original AIWorker / TTSWorker / LunaWindow above are
#   100% unchanged. LunaWindowPro subclasses the window and:
#
#     • Adds a PlanWorker thread that runs ActionExecutor
#       plans in the background with live progress
#     • Wires every Pro component together automatically:
#       core progress ring, audio ring, toasts, busy Stop
#       button, green mic, colored status, sleep state
#     • Instant local commands (no AI call): screenshot,
#       battery, system health, wi-fi, time, date, uptime,
#       open youtube/google, volume up/down
#     • Chat utilities: "clear conversation", "export
#       conversation", "copy conversation", "show stats",
#       "help", "start demo"
#     • Live header clock + task progress strip with a
#       Stop button (uses TaskProgress style)
#     • New states rendered: processing/success/error/
#       alert/sleep → core colors + status label colors
#     • Error states flash red then revert automatically
#     • Ctrl+L clear, Ctrl+E export shortcuts
#     • Click the holographic core → toggle voice mode
#     • Voice Pro features activated: wake word, idle
#       timeout, audio level feed, notices
#     • Session stats + plan results spoken via TTS
#
#   Drop-in: the alias at the bottom makes every import of
#   LunaWindow resolve to the Pro version.
#
# ============================================================
# ============================================================

import datetime

from PySide6.QtCore import QTimer

from PySide6.QtGui import (
    QKeySequence,
    QShortcut,
)

from PySide6.QtWidgets import (
    QProgressBar,
    QPushButton,
)


def _main_repolish(widget):

    widget.style().unpolish(widget)

    widget.style().polish(widget)


# ============================================================
# PLAN WORKER
# ============================================================


class PlanWorker(QThread):

    step_progress = Signal(int, int, str, str)

    plan_finished = Signal(list)

    plan_error = Signal(str)

    def __init__(self, plan):

        super().__init__()

        self.plan = plan

        self._cancelled = (
            threading.Event()
        )

    def cancel(self):

        self._cancelled.set()

        self.requestInterruption()

    @property
    def cancelled(self):

        return (
            self._cancelled.is_set()
        )

    def run(self):

        try:

            def on_progress(
                index,
                total,
                action,
                result,
            ):

                if self._cancelled.is_set():
                    return

                self.step_progress.emit(
                    int(index),
                    int(total),
                    str(
                        action.get(
                            "action",
                            "step"
                        )
                    ),
                    str(result),
                )

            results = (
                ActionExecutor.execute(
                    self.plan,
                    progress_callback=on_progress,
                )
            )

            if self._cancelled.is_set():
                return

            self.plan_finished.emit(
                results or []
            )

        except Exception as error:

            if not self._cancelled.is_set():

                self.plan_error.emit(
                    str(error)
                )


# ============================================================
# LUNA WINDOW PRO
# ============================================================


class LunaWindowPro(LunaWindow):

    # ==================================================
    # STATUS MAPS
    # (original 4 states keep the exact original look;
    #  new states get themed colors from the STYLE sheet)
    # ==================================================

    ORIGINAL_STATUS = {
        "idle": "● ONLINE",
        "listening": "● LISTENING",
        "thinking": "● THINKING",
        "speaking": "● SPEAKING",
    }

    NEW_STATE_STATUS = {
        "processing": ("StatusProcessing", "● WORKING"),
        "success": ("StatusSuccess", "● DONE"),
        "error": ("StatusError", "● ERROR"),
        "alert": ("StatusAlert", "● ATTENTION"),
        "sleep": ("StatusSleep", "● SLEEPING"),
    }

    # ==================================================
    # INSTANT COMMANDS → ActionExecutor plans
    # (answered without an AI call)
    # ==================================================

    INSTANT_PLANS = [
        (
            {
                "screenshot",
                "take a screenshot",
                "take screenshot",
            },
            [{"action": "take_screenshot"}],
        ),
        (
            {
                "battery",
                "battery status",
                "battery level",
                "check battery",
                "what's my battery level",
                "what is my battery level",
                "how much battery do i have",
            },
            [{"action": "battery_status"}],
        ),
        (
            {
                "system health",
                "system status",
                "cpu status",
                "how's my cpu",
                "performance",
                "ram usage",
            },
            [{"action": "system_health"}],
        ),
        (
            {
                "wifi status",
                "wi-fi status",
                "wifi info",
                "wi-fi info",
                "check wifi",
            },
            [{"action": "wifi_status"}],
        ),
        (
            {
                "scan wifi",
                "wifi networks",
                "list wifi networks",
                "nearby wifi",
            },
            [{"action": "wifi_scan"}],
        ),
        (
            {
                "time",
                "what time is it",
                "current time",
                "tell me the time",
            },
            [{"action": "get_time"}],
        ),
        (
            {
                "date",
                "what's the date",
                "what is the date",
                "today's date",
                "what day is it",
            },
            [{"action": "get_date"}],
        ),
        (
            {
                "uptime",
                "how long have you been on",
            },
            [{"action": "uptime"}],
        ),
        (
            {
                "open youtube",
                "launch youtube",
            },
            [
                {
                    "action": "open_website",
                    "target": "https://www.youtube.com",
                }
            ],
        ),
        (
            {
                "open google",
                "launch google",
            },
            [
                {
                    "action": "open_website",
                    "target": "https://www.google.com",
                }
            ],
        ),
        (
            {
                "volume up",
                "louder",
            },
            [{"action": "volume_up"}],
        ),
        (
            {
                "volume down",
                "quieter",
            },
            [{"action": "volume_down"}],
        ),
    ]

    def __init__(self):

        super().__init__()

        # -----------------------------
        # PLAN EXECUTION
        # -----------------------------

        self.plan_worker = None

        self.speak_plan_results = True

        # -----------------------------
        # VOICE PRO SETTINGS
        # -----------------------------

        self._voice_idle_timeout = 0

        self._voice_wake_required = False

        self.last_voice_stats = {}

        # -----------------------------
        # SESSION STATS
        # -----------------------------

        self.session_stats = {
            "text_messages": 0,
            "ai_requests": 0,
            "plans_run": 0,
            "errors": 0,
        }

        # -----------------------------
        # TRANSIENT STATE REVERT
        # -----------------------------

        self._state_revert_timer = QTimer(
            self
        )

        self._state_revert_timer.setSingleShot(
            True
        )

        self._state_revert_timer.timeout.connect(
            self._revert_transient_state
        )

        # -----------------------------
        # HEADER CLOCK
        # -----------------------------

        self._build_clock()

        # -----------------------------
        # PLAN PROGRESS STRIP
        # -----------------------------

        self._build_plan_strip()

        # -----------------------------
        # EXTRA WIRING
        # -----------------------------

        self._connect_extras()

    # ==================================================
    # BUILD: HEADER CLOCK
    # ==================================================

    def _build_clock(self):

        self.clock_label = QLabel(
            "--:--"
        )

        self.clock_label.setObjectName(
            "Clock"
        )

        try:

            root = (
                self.centralWidget().layout()
            )

            header_item = (
                root.itemAt(0)
            )

            header = (
                header_item.layout()
                if header_item
                else None
            )

            if header is not None:

                header.insertWidget(
                    2,
                    self.clock_label,
                )

        except Exception as error:

            print(
                f"[LUNA] Clock skipped: {error}"
            )

        self._clock_timer = QTimer(self)

        self._clock_timer.timeout.connect(
            self._update_clock
        )

        self._clock_timer.start(1000)

        self._update_clock()

    def _update_clock(self):

        self.clock_label.setText(
            datetime.datetime.now()
            .strftime("%H:%M")
        )

    # ==================================================
    # BUILD: PLAN PROGRESS STRIP
    # ==================================================

    def _build_plan_strip(self):

        self.plan_strip = QWidget()

        strip_layout = QHBoxLayout(
            self.plan_strip
        )

        strip_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        strip_layout.setSpacing(
            12,
        )

        self.plan_label = QLabel(
            "Working..."
        )

        self.plan_label.setObjectName(
            "Subtitle"
        )

        self.plan_bar = QProgressBar()

        self.plan_bar.setObjectName(
            "TaskProgress"
        )

        self.plan_bar.setRange(
            0,
            1,
        )

        self.plan_bar.setValue(
            0,
        )

        self.plan_cancel = QPushButton(
            "✕ Stop"
        )

        self.plan_cancel.setObjectName(
            "WindowButton"
        )

        self.plan_cancel.setCursor(
            Qt.PointingHandCursor
        )

        self.plan_cancel.clicked.connect(
            lambda: self.stop_all(
                "plan-button"
            )
        )

        strip_layout.addWidget(
            self.plan_label
        )

        strip_layout.addWidget(
            self.plan_bar,
            1,
        )

        strip_layout.addWidget(
            self.plan_cancel
        )

        self.plan_strip.setVisible(
            False
        )

        try:

            root = (
                self.centralWidget().layout()
            )

            # between the header (0) and the body (1)

            root.insertWidget(
                1,
                self.plan_strip,
            )

        except Exception as error:

            print(
                f"[LUNA] Plan strip skipped: {error}"
            )

    # ==================================================
    # CONNECT: EXTRA SIGNALS + SHORTCUTS
    # ==================================================

    def _connect_extras(self):

        # ChatInputPro signals

        self.chat_input.stop_requested.connect(
            lambda: self.stop_all(
                "stop-button"
            )
        )

        self.chat_input.escape_pressed.connect(
            self._on_input_escape
        )

        # LunaCorePro click → toggle voice

        self.core.core_clicked.connect(
            self.toggle_voice
        )

        # Keyboard shortcuts

        clear_shortcut = QShortcut(
            QKeySequence("Ctrl+L"),
            self,
        )

        clear_shortcut.activated.connect(
            self.clear_chat
        )

        export_shortcut = QShortcut(
            QKeySequence("Ctrl+E"),
            self,
        )

        export_shortcut.activated.connect(
            self.export_chat
        )

    # ==================================================
    # HELPERS
    # ==================================================

    def _any_busy(self):

        return (
            self.ai_worker is not None
            or self.tts_worker is not None
            or self.plan_worker is not None
            or self.voice_worker is not None
        )

    @staticmethod
    def _normalize_command(text):

        return (
            str(text)
            .lower()
            .strip()
            .rstrip("?.!,")
        )

    def _match_instant_plan(
        self,
        normalized,
    ):

        for phrases, plan in (
            self.INSTANT_PLANS
        ):

            if normalized in phrases:

                return [
                    dict(step)
                    for step in plan
                ]

        return None

    def _on_input_escape(self):

        if self._any_busy():

            self.stop_all("escape")

    def _revert_transient_state(self):

        if self._any_busy():
            return

        if (
            self.core.state
            in ("success", "error", "alert")
        ):

            self.set_state("idle")

    def _show_plan_ui(self, total):

        self.plan_bar.setRange(
            0,
            total,
        )

        self.plan_bar.setValue(0)

        self.plan_label.setText(
            "Working..."
        )

        self.plan_strip.setVisible(True)

    def _hide_plan_ui(self):

        self.plan_strip.setVisible(False)

    def _store_voice_stats(self, stats):

        try:

            self.last_voice_stats = (
                dict(stats)
            )

        except Exception:

            pass

    # ==================================================
    # PLAN EXECUTION (public API)
    # ==================================================

    def execute_plan(
        self,
        plan,
    ):

        if self.plan_worker is not None:

            print(
                "[LUNA] A plan is already running."
            )

            return False

        if (
            self.ai_worker is not None
            or self.tts_worker is not None
            or self.voice_worker is not None
        ):

            print(
                "[LUNA] LUNA is busy — "
                "plan not started."
            )

            return False

        if isinstance(plan, list):

            actions = plan

        elif isinstance(plan, dict):

            actions = plan.get(
                "actions",
                [],
            )

        else:

            return False

        actions = [
            action
            for action in actions
            if isinstance(action, dict)
        ]

        if not actions:

            return False

        total = len(actions)

        self.conversation.add_status_message(
            f"Running {total} step"
            + ("s" if total != 1 else "")
            + "…",
            "info",
        )

        self._show_plan_ui(total)

        self.set_state("processing")

        self.chat_input.set_busy(True)

        self.plan_worker = PlanWorker(
            {"actions": actions}
        )

        self.plan_worker.step_progress.connect(
            self.plan_step
        )

        self.plan_worker.plan_finished.connect(
            self.plan_done
        )

        self.plan_worker.plan_error.connect(
            self.plan_error
        )

        # clears the reference only after the
        # thread has truly finished running

        self.plan_worker.finished.connect(
            self._plan_thread_finished
        )

        self.plan_worker.start()

        return True

    def plan_step(
        self,
        index,
        total,
        action_name,
        result,
    ):

        self.core.set_progress(
            index / float(total)
        )

        self.plan_bar.setValue(index)

        text = (
            f"{index}/{total} · {result}"
        )

        if len(text) > 90:

            text = text[:87] + "…"

        self.plan_label.setText(text)

        self.conversation.add_action_result(
            result
        )

        self.core.show_message(
            result,
            2.5,
        )

    def plan_done(self, results):

        self._hide_plan_ui()

        self.core.clear_progress()

        self.session_stats[
            "plans_run"
        ] += 1

        self.conversation.add_status_message(
            "All steps completed.",
            "success",
        )

        last_result = ""

        if results:

            try:

                last_result = str(
                    results[-1].get(
                        "result",
                        "",
                    )
                )

            except Exception:

                last_result = ""

        if (
            last_result
            and len(last_result) <= 140
            and self.speak_plan_results
        ):

            # tts_finished will restore input + idle

            self._speak_text(last_result)

        else:

            self.chat_input.set_busy(False)

            self.enable_input()

            self.set_state("success")

            self._state_revert_timer.start(
                1600
            )

    def plan_error(self, error):

        print(
            f"❌ Plan error: {error}"
        )

        self._hide_plan_ui()

        self.core.clear_progress()

        self.conversation.add_status_message(
            f"Plan failed: {error}",
            "error",
        )

        self.chat_input.set_busy(False)

        self.enable_input()

        self.set_state("error")

        self._state_revert_timer.start(
            1800
        )

    def _plan_thread_finished(self):

        self.plan_worker = None

    def _speak_text(self, text):

        if self.tts_worker is not None:
            return

        generation = (
            self._generation_guard.next()
        )

        self._active_tts_generation = (
            generation
        )

        self.set_state("speaking")

        self.tts_worker = TTSWorker(
            text
        )

        self.tts_worker.generation = (
            generation
        )

        self.tts_worker.finished.connect(
            lambda gen=generation: self.tts_finished(
                gen
            )
        )

        self.tts_worker.error.connect(
            lambda err, gen=generation: self.tts_error(
                err,
                gen,
            )
        )

        self.tts_worker.start()

    # ==================================================
    # TEXT PIPELINE (instant commands, then original)
    # ==================================================

    def handle_text(
        self,
        message,
    ):

        text = str(message).strip()

        normalized = (
            self._normalize_command(text)
        )

        # ----------------------------------------------
        # CHAT UTILITIES — always available
        # ----------------------------------------------

        if normalized in {
            "clear conversation",
            "clear chat",
            "clear messages",
        }:

            self.clear_chat()

            return

        if normalized in {
            "export conversation",
            "save conversation",
            "export chat",
        }:

            self.export_chat()

            return

        if normalized in {
            "copy conversation",
            "copy chat",
        }:

            result = (
                self.conversation.copy_conversation()
            )

            self.conversation.add_status_message(
                result,
                "success",
            )

            return

        if normalized in {
            "show stats",
            "session stats",
            "stats",
        }:

            self._show_stats()

            return

        if normalized in {
            "help",
            "what can you do",
            "commands",
        }:

            self._show_help()

            return

        if normalized in {
            "start demo",
            "demo mode",
            "demo",
        }:

            self.core.start_demo()

            self.core.show_message(
                "Demo mode — click the core "
                "or say stop demo",
                3.5,
            )

            return

        if normalized in {
            "stop demo",
        }:

            self.core.stop_demo()

            return

        # ----------------------------------------------
        # INSTANT COMMANDS — no AI call
        # ----------------------------------------------

        instant_plan = (
            self._match_instant_plan(
                normalized
            )
        )

        if instant_plan is not None:

            if self._any_busy():

                print(
                    "[LUNA] Busy — instant "
                    "command ignored."
                )

                return

            print()
            print(
                f"👤 You: {text}"
            )

            self.conversation.add_user_message(
                text
            )

            self.execute_plan(instant_plan)

            return

        # ----------------------------------------------
        # EVERYTHING ELSE — original pipeline
        # ----------------------------------------------

        super().handle_text(message)

        if self.ai_worker is not None:

            # AI request actually started —
            # turn Send into a Stop button

            self.chat_input.set_busy(True)

            self.session_stats[
                "text_messages"
            ] += 1

            self.session_stats[
                "ai_requests"
            ] += 1

    # ==================================================
    # STATE (adds themed states, keeps original look)
    # ==================================================

    def set_state(
        self,
        state,
    ):

        super().set_state(state)

        key = str(state).lower()

        if key in self.NEW_STATE_STATUS:

            object_name, status_text = (
                self.NEW_STATE_STATUS[key]
            )

            self.status.setText(status_text)

            if (
                self.status.objectName()
                != object_name
            ):

                self.status.setObjectName(
                    object_name
                )

                _main_repolish(
                    self.status
                )

        elif key in self.ORIGINAL_STATUS:

            if (
                self.status.objectName()
                != "Status"
            ):

                self.status.setObjectName(
                    "Status"
                )

                _main_repolish(
                    self.status
                )

    # ==================================================
    # INPUT LIFECYCLE HOOKS
    # ==================================================

    def enable_input(self):

        super().enable_input()

        self.chat_input.set_busy(False)

    def ai_error(self, error):

        worker = self.sender()

        if isinstance(worker, AIWorker):

            if (
                worker.request_id
                != self._active_request_id
            ):
                return

            if (
                not self._generation_guard
                .is_current(
                    worker.generation
                )
            ):
                return

            if worker.cancelled:
                return

        super().ai_error(error)

        self.session_stats[
            "errors"
        ] += 1

        self.set_state("error")

        self._state_revert_timer.start(
            1800
        )

    # ==================================================
    # VOICE LIFECYCLE HOOKS (activate Pro features)
    # ==================================================

    def start_voice(self):

        super().start_voice()

        worker = self.voice_worker

        if worker is None:
            return

        # VoiceWorkerPro extras (guarded so the
        # window also works with a plain worker)

        if hasattr(worker, "notice"):

            worker.notice.connect(
                self.core.show_message
            )

        if hasattr(worker, "audio_level"):

            worker.audio_level.connect(
                self.core.set_audio_level
            )

        if hasattr(worker, "stats_updated"):

            worker.stats_updated.connect(
                self._store_voice_stats
            )

        if hasattr(
            worker,
            "set_idle_timeout",
        ):

            worker.set_idle_timeout(
                self._voice_idle_timeout
            )

        if (
            hasattr(
                worker,
                "set_wake_word_required",
            )
            and self._voice_wake_required
        ):

            worker.set_wake_word_required(
                True
            )

        self.chat_input.set_listening(True)

    def stop_voice(self):

        super().stop_voice()

        self.chat_input.set_listening(False)

        self.core.set_audio_level(0.0)

    def voice_finished(self):

        super().voice_finished()

        self.chat_input.set_listening(False)

        self.core.set_audio_level(0.0)

    # ==================================================
    # VOICE PRO CONFIGURATION (public API)
    # ==================================================

    def set_voice_idle_timeout(self, seconds):

        self._voice_idle_timeout = max(
            0,
            int(seconds),
        )

        worker = self.voice_worker

        if (
            worker is not None
            and hasattr(
                worker,
                "set_idle_timeout",
            )
        ):

            worker.set_idle_timeout(
                self._voice_idle_timeout
            )

    def set_wake_word_required(self, required):

        self._voice_wake_required = bool(
            required
        )

        worker = self.voice_worker

        if (
            worker is not None
            and hasattr(
                worker,
                "set_wake_word_required",
            )
        ):

            worker.set_wake_word_required(
                self._voice_wake_required
            )

    # ==================================================
    # CHAT UTILITIES
    # ==================================================

    def clear_chat(self):

        self.conversation.clear_messages()

        self.conversation.add_status_message(
            "Conversation cleared.",
            "info",
        )

    def export_chat(self):

        result = (
            self.conversation.export_conversation()
        )

        tone = (
            "success"
            if "saved" in result.lower()
            else "info"
        )

        self.conversation.add_status_message(
            result,
            tone,
        )

        self.core.show_message(
            "Conversation exported",
            3.0,
        )

    def _show_stats(self):

        lines = ["📊 Session stats:"]

        stats = dict(
            self.session_stats
        )

        lines.append(
            f"• Text messages: "
            f"{stats.get('text_messages', 0)}"
        )

        lines.append(
            f"• AI requests: "
            f"{stats.get('ai_requests', 0)}"
        )

        lines.append(
            f"• Plans run: "
            f"{stats.get('plans_run', 0)}"
        )

        lines.append(
            f"• Errors: "
            f"{stats.get('errors', 0)}"
        )

        worker = self.voice_worker

        if (
            worker is not None
            and hasattr(worker, "get_stats")
        ):

            try:

                voice_stats = (
                    worker.get_stats()
                )

                lines.append(
                    f"• Voice messages: "
                    f"{voice_stats.get('user_messages', 0)}"
                )

                lines.append(
                    f"• Voice replies: "
                    f"{voice_stats.get('luna_responses', 0)}"
                )

                lines.append(
                    f"• Fast commands: "
                    f"{voice_stats.get('fast_commands', 0)}"
                )

                lines.append(
                    f"• Barge-ins: "
                    f"{voice_stats.get('barge_ins', 0)}"
                )

                lines.append(
                    f"• Session length: "
                    f"{voice_stats.get('session_duration', '?')}"
                )

            except Exception:

                pass

        self.conversation.add_luna_message(
            "\n".join(lines)
        )

    def _show_help(self):

        lines = [
            "Here's what I can do:",
            "",
            "⚡ Instant (no AI needed):",
            "• screenshot · battery · system health",
            "• wi-fi status · scan wifi",
            "• time · date · uptime",
            "• open youtube · open google",
            "• volume up · volume down",
            "",
            "🧹 Chat:",
            "• clear conversation · export conversation",
            "• copy conversation · show stats · help",
            "",
            "🎙️ Voice mode: click the core or the mic",
            "⌨️ Shortcuts: Esc = stop · Ctrl+L = clear · "
            "Ctrl+E = export",
        ]

        self.conversation.add_luna_message(
            "\n".join(lines)
        )

    # ==================================================
    # CLOSE (stops the plan worker too)
    # ==================================================

    def closeEvent(
        self,
        event,
    ):

        if self.plan_worker is not None:

            print(
                "[LUNA] Closing: stopping plan..."
            )

            try:

                self.plan_worker.cancel()

            except Exception:

                pass

            self.plan_worker.wait(1500)

        super().closeEvent(event)


# ------------------------------------------------------------
# DROP-IN UPGRADE
# Anything that imports LunaWindow from this file now gets
# the extended version automatically (same API, more power).
# Delete the next line to keep using the original window.
# ------------------------------------------------------------

LunaWindow = LunaWindowPro