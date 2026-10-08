import threading

from PySide6.QtCore import (
    QThread,
    Signal,
)

from voice.speech_to_text import SpeechToText
from voice.text_to_speech import TextToSpeech

from core.agent import LunaAgent
from core.barge_in import BargeInListener
from core.stop_control import GenerationGuard


class VoiceWorker(QThread):

    state_changed = Signal(str)

    user_text = Signal(str)

    luna_response = Signal(str)

    error = Signal(str)

    def __init__(self):

        super().__init__()

        self.running = True

        # ------------------------------------------------
        # LOAD ONCE
        # ------------------------------------------------

        self.stt = SpeechToText()

        self.tts = TextToSpeech()

        self.agent = LunaAgent()

        self.current_language = "unknown"

        self.language_probability = 0.0
        self.barge_in = None
        self._barge_stop_event = threading.Event()
        self._speech_guard = GenerationGuard()
        self._active_speech_generation = 0

    # ==================================================
    # RUN
    # ==================================================

    def run(self):

        print(
            "\n🌙 LUNA Multilingual Voice Mode"
        )

        while self.running:

            try:

                # ------------------------------------------
                # LISTEN
                # ------------------------------------------

                self.state_changed.emit(
                    "listening"
                )

                text = self.stt.listen()

                if not self.running:

                    break

                if not text:

                    continue

                text = str(
                    text
                ).strip()

                if not text:

                    continue

                # ------------------------------------------
                # LANGUAGE
                # ------------------------------------------

                self.current_language = (
                    getattr(
                        self.stt,
                        "last_language",
                        "unknown"
                    )
                    or "unknown"
                )

                self.language_probability = float(
                    getattr(
                        self.stt,
                        "last_language_probability",
                        0.0
                    )
                    or 0.0
                )

                print(
                    f"🌐 Language: "
                    f"{self.current_language}"
                )

                print(
                    f"🌐 Confidence: "
                    f"{self.language_probability:.2f}"
                )

                # ------------------------------------------
                # SHOW USER
                # ------------------------------------------

                self.user_text.emit(
                    text
                )

                # ------------------------------------------
                # EXIT
                # ------------------------------------------

                command = (
                    text.lower()
                    .strip()
                )

                # A plain STOP ends voice mode silently. The UI microphone
                # button can also stop speech while TTS is playing.
                if command in {
                    "stop",
                    "stop luna",
                    "stop speaking",
                }:
                    self.running = False
                    try:
                        self.tts.stop()
                    except Exception:
                        pass
                    break

                if command in [
                    "exit",
                    "quit",
                    "goodbye",
                    "stop voice",
                    "stop voice mode",
                ]:

                    self.state_changed.emit(
                        "speaking"
                    )

                    language = (
                        self.current_language
                        if self.current_language
                        != "unknown"
                        else "en"
                    )

                    self.tts.speak(
                        "Goodbye. See you later.",
                        language=language
                    )

                    self.running = False

                    break

                # ------------------------------------------
                # THINKING
                # ------------------------------------------

                self.state_changed.emit(
                    "thinking"
                )

                response = self.agent.chat(
                    text,
                    model="groq"
                )

                if not self.running:

                    break

                if not response:

                    continue

                response = str(
                    response
                ).strip()

                if not response:

                    continue

                # ------------------------------------------
                # SHOW RESPONSE IMMEDIATELY
                # ------------------------------------------

                self.luna_response.emit(
                    response
                )

                # ------------------------------------------
                # DETECT RESPONSE LANGUAGE
                # ------------------------------------------

                response_language = (
                    self.tts.detect_text_language(
                        response
                    )
                )

                # If response contains native script,
                # trust the actual response language.

                has_native_script = (
                    self._contains_native_script(
                        response
                    )
                )

                if (
                    not has_native_script
                    and
                    self.current_language
                    != "unknown"
                    and
                    self.language_probability
                    >= 0.65
                ):

                    response_language = (
                        self.current_language
                    )

                print(
                    f"🌐 Response language: "
                    f"{response_language}"
                )

                # ------------------------------------------
                # SPEAK
                # ------------------------------------------

                self.state_changed.emit(
                    "speaking"
                )

                # Phase 13.2: every speech response gets a generation token.
                # A late STOP callback from an old response cannot affect a
                # newer response because the callback verifies the token.
                speech_generation = self._speech_guard.next()
                self._active_speech_generation = speech_generation
                self._barge_stop_event.clear()

                self.barge_in = BargeInListener(
                    transcribe=self.stt._transcribe,
                    on_stop=lambda detected, gen=speech_generation: self._on_barge_stop(detected, gen),
                )
                self.barge_in.start()

                try:
                    self.tts.speak(
                        response,
                        language=response_language
                    )
                finally:
                    # Invalidate this speech before stopping the listener so
                    # a racing callback cannot touch a completed/new response.
                    self._active_speech_generation = 0
                    if self.barge_in is not None:
                        self.barge_in.stop()
                    self.barge_in = None

                if self._barge_stop_event.is_set() and self.running:
                    print("[LUNA] Voice barge-in handled; returning to listening.")

                if self.running:
                    self.state_changed.emit("listening")

            except Exception as error:

                print(
                    f"❌ Voice worker error: "
                    f"{error}"
                )

                self.error.emit(
                    str(error)
                )

                self.state_changed.emit(
                    "idle"
                )

        try:
            self.agent.shutdown()
        except Exception as error:
            print(f"[LUNA] Voice agent shutdown warning: {error}")

        self.state_changed.emit(
            "idle"
        )

    def _on_barge_stop(self, detected_text: str = "stop", generation: int = 0):
        """Handle a spoken STOP only when it belongs to active speech."""
        if not self.running:
            return

        if generation and generation != self._active_speech_generation:
            print("[LUNA] Ignoring stale barge-in STOP callback.")
            return

        if generation and not self._speech_guard.is_current(generation):
            print("[LUNA] Ignoring invalidated barge-in STOP callback.")
            return

        print(f"🛑 LUNA voice barge-in: {detected_text}")
        self._barge_stop_event.set()

        # Immediately stop audio. Voice mode remains active so the worker can
        # return to normal microphone listening after the current response.
        try:
            self.tts.stop()
        except Exception:
            pass

    # ==================================================
    # NATIVE SCRIPT CHECK
    # ==================================================

    def _contains_native_script(
        self,
        text
    ):

        for char in text:

            code = ord(char)

            if (
                0x0900 <= code <= 0x0DFF
                or
                0x0600 <= code <= 0x06FF
                or
                0x3040 <= code <= 0x30FF
                or
                0xAC00 <= code <= 0xD7AF
                or
                0x4E00 <= code <= 0x9FFF
            ):

                return True

        return False

    # ==================================================
    # STOP
    # ==================================================

    def stop(self):

        print(
            "🛑 Stopping LUNA voice worker..."
        )

        self.running = False
        self._speech_guard.invalidate()
        self._active_speech_generation = 0

        self.requestInterruption()

        if self.barge_in is not None:
            try:
                self.barge_in.stop()
            except Exception:
                pass
            self.barge_in = None

        try:
            self.tts.stop()
        except Exception:
            pass

        # Also stop the process-global pygame music stream.
        try:
            import pygame
            pygame.mixer.music.stop()
        except Exception:
            pass


# ============================================================
# ============================================================
#
#   🌙 LUNA VOICE WORKER PRO — EXTENSIONS (APPEND ONLY)
#
#   The original VoiceWorker above is 100% unchanged.
#   VoiceWorkerPro subclasses it and wraps stt/tts/agent to
#   add:
#
#     • Wake word mode — "hey LUNA" / "ok LUNA" to wake,
#       "go to sleep" to doze (UI shows the sleep state)
#     • Idle timeout — auto-sleep after N silent minutes
#     • Instant quick commands — time, date, battery,
#       volume up/down answered WITHOUT the AI call
#     • "Repeat that" — replays the last response free
#     • Voice-controlled mute — "mute" / "unmute"
#     • submit_text() — typed chat input rides the same
#       voice pipeline (mic and keyboard unified)
#     • Mute mode — TTS skipped, replies stay in the UI
#     • Session transcript + export_session()
#     • Live stats — messages, barge-ins, wake-ups,
#       languages used, session duration
#     • audio_level signal — feed LunaCorePro's ring
#       (synthetic speech-wave emitted while talking)
#     • notice signal — toasts for sleep/wake/mute events
#
#   Zero new dependencies (psutil optional for battery).
#
# ============================================================
# ============================================================

import math
import queue
import time
import datetime

from pathlib import Path

from PySide6.QtCore import QTimer


def _voice_normalize(text):

    cleaned = str(
        text
    ).lower().strip()

    return cleaned.strip("?.!,")


class VoiceWorkerPro(VoiceWorker):

    # ==================================================
    # NEW SIGNALS
    # ==================================================

    notice = Signal(str)

    audio_level = Signal(float)

    wake_word_detected = Signal()

    stats_updated = Signal(dict)

    # ==================================================
    # PHRASE TABLES
    # ==================================================

    WAKE_WORDS = {
        "luna",
        "hey luna",
        "hi luna",
        "hello luna",
        "ok luna",
        "okay luna",
        "yo luna",
    }

    SLEEP_TRIGGERS = {
        "go to sleep",
        "go to sleep luna",
        "sleep luna",
        "luna sleep",
        "sleep now",
        "take a nap",
    }

    MUTE_TRIGGERS = {
        "mute",
        "mute luna",
        "be quiet",
        "quiet mode",
        "stop talking",
    }

    UNMUTE_TRIGGERS = {
        "unmute",
        "unmute luna",
        "talk to me",
        "start talking",
    }

    REPEAT_TRIGGERS = {
        "repeat",
        "repeat that",
        "repeat please",
        "say that again",
        "say it again",
        "can you repeat",
        "can you repeat that",
        "what did you say",
    }

    def __init__(self):

        super().__init__()

        # -----------------------------
        # SLEEP / WAKE STATE
        # -----------------------------

        self._awake = True

        self.wake_word_required = False

        self.idle_timeout_seconds = 0

        self._last_activity = (
            time.monotonic()
        )

        # -----------------------------
        # MUTE
        # -----------------------------

        self.muted = False

        # -----------------------------
        # TYPED TEXT INJECTION
        # -----------------------------

        self._text_queue = queue.Queue()

        # -----------------------------
        # MEMORY + STATS
        # -----------------------------

        self.conversation_log = []

        self._last_response = ""

        self._stats_lock = (
            threading.Lock()
        )

        self.stats = {
            "started_at": datetime.datetime.now()
            .strftime("%Y-%m-%d %H:%M:%S"),

            "user_messages": 0,

            "luna_responses": 0,

            "fast_commands": 0,

            "repeats": 0,

            "barge_ins": 0,

            "wakeups": 0,

            "sleeps": 0,

            "languages": {},
        }

        self._session_start = (
            time.monotonic()
        )

        # -----------------------------
        # QUICK COMMANDS
        # -----------------------------

        self._custom_quick = []

        self._builtin_quick = [
            (
                [
                    "what time is it",
                    "what's the time",
                    "what is the time",
                    "tell me the time",
                    "current time",
                ],
                self._quick_time,
            ),
            (
                [
                    "what's the date",
                    "what is the date",
                    "what day is it",
                    "tell me the date",
                    "what's today's date",
                ],
                self._quick_date,
            ),
            (
                [
                    "what's my battery level",
                    "what is my battery level",
                    "battery status",
                    "battery level",
                    "how much battery do i have",
                    "check battery",
                ],
                self._quick_battery,
            ),
            (
                [
                    "volume up",
                    "turn the volume up",
                    "louder",
                ],
                self._quick_volume_up,
            ),
            (
                [
                    "volume down",
                    "turn the volume down",
                    "quieter",
                ],
                self._quick_volume_down,
            ),
        ]

        # -----------------------------
        # AUDIO LEVEL FEED
        # -----------------------------

        self._audio_source = None

        self._synth_phase = 0.0

        self._current_state = "idle"

        self._audio_timer = QTimer(self)

        self._audio_timer.timeout.connect(
            self._poll_audio
        )

        self._audio_timer.start(100)

        # -----------------------------
        # WRAP COMPONENTS
        # (original methods preserved)
        # -----------------------------

        self._original_listen = (
            self.stt.listen
        )

        self.stt.listen = (
            self._wrapped_listen
        )

        self._original_chat = (
            self.agent.chat
        )

        self.agent.chat = (
            self._wrapped_chat
        )

        self._original_speak = (
            self.tts.speak
        )

        self.tts.speak = (
            self._wrapped_speak
        )

        base_barge = (
            self._on_barge_stop
        )

        def _barge_wrapper(
            detected_text="stop",
            generation=0,
        ):

            with self._stats_lock:

                self.stats[
                    "barge_ins"
                ] += 1

            return base_barge(
                detected_text,
                generation,
            )

        self._on_barge_stop = (
            _barge_wrapper
        )

        # -----------------------------
        # TRACKERS (run in main thread)
        # -----------------------------

        self.state_changed.connect(
            self._track_state
        )

        self.user_text.connect(
            self._track_user_text
        )

        self.luna_response.connect(
            self._track_response
        )

    # ==================================================
    # NORMALIZATION + MATCHING
    # ==================================================

    def _is_wake_phrase(self, normalized):

        for word in self.WAKE_WORDS:

            if (
                normalized == word
                or normalized.startswith(
                    word + " "
                )
                or normalized.startswith(
                    word + ","
                )
            ):

                return True

        return False

    def _match_quick_command(self, normalized):

        for phrases, handler in (
            self._custom_quick
            + self._builtin_quick
        ):

            for phrase in phrases:

                if (
                    normalized == phrase
                    or normalized.startswith(
                        phrase + " "
                    )
                ):

                    try:

                        return str(
                            handler()
                        )

                    except Exception as error:

                        print(
                            f"[LUNA] Quick command error: {error}"
                        )

                        return (
                            "That quick command "
                            "didn't work."
                        )

        return None

    # ==================================================
    # QUICK COMMAND HANDLERS
    # ==================================================

    def _quick_time(self):

        now = datetime.datetime.now()

        return (
            "It's "
            + now.strftime("%I:%M %p")
            .lstrip("0")
            + "."
        )

    def _quick_date(self):

        today = datetime.date.today()

        return (
            "Today is "
            + today.strftime("%A, %B %d, %Y")
            + "."
        )

    def _quick_battery(self):

        try:

            import psutil

            battery = (
                psutil.sensors_battery()
            )

            if battery is None:

                return (
                    "I couldn't find a "
                    "battery on this machine."
                )

            percent = round(
                battery.percent
            )

            if battery.power_plugged:

                return (
                    f"You're at {percent} "
                    f"percent and charging."
                )

            return (
                f"You're at {percent} "
                f"percent battery."
            )

        except Exception:

            return (
                "I couldn't read the "
                "battery level."
            )

    def _tap_volume(self, virtual_key, presses=6):

        try:

            import ctypes

            for _ in range(presses):

                ctypes.windll.user32.keybd_event(
                    virtual_key, 0, 0, 0
                )

                ctypes.windll.user32.keybd_event(
                    virtual_key, 0, 2, 0
                )

            return True

        except Exception:

            return False

    def _quick_volume_up(self):

        if self._tap_volume(0xAF):

            return "Turning the volume up."

        return (
            "Volume control is only "
            "available on Windows."
        )

    def _quick_volume_down(self):

        if self._tap_volume(0xAE):

            return "Turning the volume down."

        return (
            "Volume control is only "
            "available on Windows."
        )

    # ==================================================
    # WRAPPED LISTEN
    # (wake word, sleep, mute, injected text)
    # ==================================================

    def _wrapped_listen(self):

        # 1) Typed text injected via
        #    submit_text() jumps the queue.

        try:

            injected = (
                self._text_queue.get_nowait()
            )

            self._touch_activity()

            return injected

        except queue.Empty:

            pass

        # 2) Idle auto-sleep.

        if (
            self._awake
            and self.idle_timeout_seconds > 0
            and (
                time.monotonic()
                - self._last_activity
            )
            > self.idle_timeout_seconds
        ):

            self._go_to_sleep(
                "Going to sleep to save power. "
                "Say 'hey LUNA' when you "
                "need me."
            )

        # 3) Real microphone listen.

        heard = self._original_listen()

        if not self.running:

            return heard

        text = str(
            heard or ""
        ).strip()

        if not text:

            return heard

        normalized = _voice_normalize(
            text
        )

        # 4) Asleep: only the wake word passes.

        if not self._awake:

            if self._is_wake_phrase(
                normalized
            ):

                self._wake_up()

            return ""

        # 5) Awake: voice control phrases.

        if (
            normalized
            in self.SLEEP_TRIGGERS
            or normalized.startswith(
                "go to sleep"
            )
        ):

            self._go_to_sleep()

            return ""

        if normalized in self.MUTE_TRIGGERS:

            self.set_muted(True)

            return ""

        if normalized in self.UNMUTE_TRIGGERS:

            self.set_muted(False)

            return ""

        # 6) Normal speech — original behavior.

        self._touch_activity()

        return heard

    # ==================================================
    # WRAPPED CHAT (quick commands + repeat)
    # ==================================================

    def _wrapped_chat(self, text, *args, **kwargs):

        normalized = _voice_normalize(
            text
        )

        reply = None

        if (
            normalized
            in self.REPEAT_TRIGGERS
            and self._last_response
        ):

            with self._stats_lock:

                self.stats[
                    "repeats"
                ] += 1

            reply = self._last_response

        else:

            quick = self._match_quick_command(
                normalized
            )

            if quick is not None:

                with self._stats_lock:

                    self.stats[
                        "fast_commands"
                    ] += 1

                reply = quick

        if reply is None:

            reply = self._original_chat(
                text,
                *args,
                **kwargs,
            )

        if reply:

            self._last_response = str(
                reply
            )

        return reply

    # ==================================================
    # WRAPPED SPEAK (mute support)
    # ==================================================

    def _wrapped_speak(self, text, *args, **kwargs):

        if self.muted:

            print(
                "[LUNA] 🔇 Muted — skipping speech."
            )

            return None

        if kwargs.get("language") is None and "language" not in kwargs:

            return self._original_speak(
                text,
                *args,
                **kwargs,
            )

        return self._original_speak(
            text,
            *args,
            **kwargs,
        )

    # ==================================================
    # SLEEP / WAKE
    # ==================================================

    def _go_to_sleep(self, message=None):

        if not self._awake:

            return

        self._awake = False

        with self._stats_lock:

            self.stats["sleeps"] += 1

        print("[LUNA] 😴 LUNA is sleeping.")

        self.notice.emit(
            message
            or "LUNA is sleeping. Say "
            "'hey LUNA' to wake me."
        )

    def _wake_up(self):

        self._awake = True

        with self._stats_lock:

            self.stats["wakeups"] += 1

        self._touch_activity()

        print("[LUNA] ⏰ Wake word detected.")

        self.wake_word_detected.emit()

        self.notice.emit("I'm awake!")

    def _touch_activity(self):

        self._last_activity = (
            time.monotonic()
        )

    # ==================================================
    # TRACKERS
    # ==================================================

    def _track_state(self, state):

        self._current_state = str(
            state
        )

        # While asleep, keep the UI in the
        # sleep state even though the loop
        # re-emits "listening" every cycle.

        if (
            not self._awake
            and state == "listening"
        ):

            QTimer.singleShot(
                0,
                lambda: self.state_changed.emit(
                    "sleep"
                ),
            )

    def _track_user_text(self, text):

        with self._stats_lock:

            self.stats[
                "user_messages"
            ] += 1

            language = (
                self.current_language
            )

            self.stats["languages"][
                language
            ] = (
                self.stats[
                    "languages"
                ].get(language, 0)
                + 1
            )

        self.conversation_log.append(
            {
                "time": datetime.datetime.now()
                .strftime("%H:%M"),

                "role": "user",

                "text": str(text),
            }
        )

    def _track_response(self, response):

        with self._stats_lock:

            self.stats[
                "luna_responses"
            ] += 1

            snapshot = dict(
                self.stats
            )

        self.conversation_log.append(
            {
                "time": datetime.datetime.now()
                .strftime("%H:%M"),

                "role": "luna",

                "text": str(response),
            }
        )

        if len(
            self.conversation_log
        ) > 500:

            self.conversation_log = (
                self.conversation_log[-500:]
            )

        self.stats_updated.emit(
            snapshot
        )

    # ==================================================
    # AUDIO LEVEL FEED
    # ==================================================

    def set_audio_level_source(self, source):

        # Optional callable returning 0.0 - 1.0
        # (e.g. your mic's RMS meter). Without
        # one, LUNA emits a synthetic speech
        # wave while speaking so the core's
        # audio ring still dances.

        self._audio_source = source

    def _poll_audio(self):

        level = 0.0

        if self._audio_source:

            try:

                level = float(
                    self._audio_source()
                )

            except Exception:

                level = 0.0

        elif (
            self._current_state
            == "speaking"
        ):

            self._synth_phase += 0.28

            level = (
                0.18
                + 0.34
                * abs(
                    math.sin(
                        self._synth_phase
                    )
                )
                * (
                    0.6
                    + 0.4
                    * math.sin(
                        self._synth_phase
                        * 0.37
                    )
                )
            )

        self.audio_level.emit(
            max(
                0.0,
                min(1.0, level),
            )
        )

    # ==================================================
    # PUBLIC API
    # ==================================================

    def submit_text(self, text):

        # Typed input rides the SAME pipeline
        # as voice: state changes, language
        # handling, quick commands, TTS.

        text = str(
            text
        ).strip()

        if text:

            self._text_queue.put(
                text
            )

    def set_wake_word_required(self, required):

        self.wake_word_required = bool(
            required
        )

        self._awake = not required

        if required:

            self.notice.emit(
                "Say 'hey LUNA' to wake me."
            )

    def set_idle_timeout(self, seconds):

        self.idle_timeout_seconds = max(
            0,
            int(seconds),
        )

    def set_muted(self, muted):

        self.muted = bool(muted)

        print(
            f"[LUNA] 🔇 Muted: {self.muted}"
        )

        self.notice.emit(
            "Muted — I'll reply in text only."
            if self.muted
            else "Unmuted — voice is back."
        )

    def register_quick_command(
        self,
        phrases,
        handler,
    ):

        # handler: callable() -> str, or a
        # plain string response.

        if isinstance(handler, str):

            text = handler

            handler = (
                lambda: text
            )

        self._custom_quick.append(
            (
                [
                    _voice_normalize(p)
                    for p in phrases
                ],
                handler,
            )
        )

    def get_stats(self):

        with self._stats_lock:

            snapshot = dict(
                self.stats
            )

            snapshot["languages"] = dict(
                self.stats["languages"]
            )

        seconds = int(
            time.monotonic()
            - self._session_start
        )

        hours = seconds // 3600

        minutes = (seconds % 3600) // 60

        snapshot["session_duration"] = (
            f"{hours}h {minutes}m"
        )

        snapshot["awake"] = self._awake

        snapshot["muted"] = self.muted

        return snapshot

    def get_conversation(self):

        return list(
            self.conversation_log
        )

    def export_session(self, path=None):

        if not self.conversation_log:

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
                    "luna_voice_"
                    + datetime.datetime.now()
                    .strftime("%Y%m%d_%H%M%S")
                    + ".txt"
                )
            )

        lines = [
            f"[{entry['time']}] "
            f"{entry['role'].upper()}: "
            f"{entry['text']}"
            for entry in self.conversation_log
        ]

        Path(path).write_text(
            "\n".join(lines),
            encoding="utf-8",
        )

        return f"Session saved to {path}."


# ------------------------------------------------------------
# DROP-IN UPGRADE
# Anything that imports VoiceWorker from this file now gets
# the extended version automatically (same API, more powers).
# Delete the next line to keep using the original worker.
# ------------------------------------------------------------

VoiceWorker = VoiceWorkerPro


# ============================================================
# QUICK WIRING EXAMPLE (uncomment to test standalone)
# ============================================================
#
# if __name__ == "__main__":
#
#     worker = VoiceWorker()
#
#     worker.notice.connect(lambda m: print("NOTICE:", m))
#     worker.audio_level.connect(lambda l: print("LEVEL:", round(l, 2)))
#     worker.user_text.connect(lambda t: print("USER:", t))
#     worker.luna_response.connect(lambda r: print("LUNA:", r))
#
#     # typed input through the same pipeline:
#     worker.submit_text("what time is it")
#
#     # or wake-word mode:
#     # worker.set_wake_word_required(True)
#
#     worker.start()
#
#     worker.exec()   # keep the thread alive for the demo