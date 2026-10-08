from voice.speech_to_text import SpeechToText
from voice.text_to_speech import TextToSpeech
from core.agent import LunaAgent

class VoiceManager:

    def __init__(self):

        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.luna = LunaAgent()

    def start(self):

        print("\n🌙 LUNA Voice Mode")
        print("=" * 50)
        print("Say 'exit' to stop.")
        print()

        while True:

            text = self.stt.listen()

            if not text:
                continue

            command = text.lower().strip()

            if command in [
                "exit",
                "quit",
                "stop",
                "goodbye"
            ]:

                self.tts.speak(
                    "Goodbye. See you later."
                )

                break

            print("\n🧠 LUNA is thinking...")

            try:

                response = self.luna.chat(
                    text,
                    model="groq"
                )

                if response:
                    self.tts.speak(response)

            except Exception as error:

                print(f"❌ AI error: {error}")

                self.tts.speak(
                    "Sorry, something went wrong."
                )


# ============================================================
# ============================================================
#
#   🌙 LUNA VOICE MANAGER PRO — EXTENSIONS (APPEND ONLY)
#
#   The original VoiceManager above is 100% unchanged.
#   VoiceManagerPro subclasses it, wraps stt/tts/luna at
#   the instance level (originals preserved), and runs an
#   enhanced session loop.
#
#   FIXES
#     • Ctrl+C crashed with a raw traceback mid-loop —
#       now exits gracefully
#     • LunaAgent.shutdown() was NEVER called — resources
#       leaked on every exit; now always runs
#     • A failing microphone raised straight out of the
#       loop and killed the session — now caught w/ backoff
#     • Empty AI responses were silently ignored — LUNA
#       now says so instead of going quiet
#     • Exit words failed when spoken with punctuation
#       ("exit.") — matching now strips punctuation
#     • Latin-script replies (French/Spanish/German…) were
#       spoken with the ENGLISH voice — Pro passes the
#       user's spoken language to TTS when confident
#     • No way to end the session from code — added a
#       thread-safe stop()
#
#   ADDITIONS
#     • Wake word gate — "hey luna" / "ok luna"
#     • Instant quick commands (no AI call): time, date,
#       battery, system health, volume up/down
#     • "repeat that" replays the last answer free
#     • Voice mute — "mute" / "unmute" (replies print)
#     • Barge-in — background listener interrupts LUNA
#       mid-sentence when you say "stop"
#     • Conversation log + export_session()
#     • Hooks: on_user_text / on_response / on_notice
#     • submit_text() — typed input rides the same pipeline
#     • register_quick_command() + get_stats() + summary
#
# ============================================================
# ============================================================

import queue
import time
import datetime

from pathlib import Path


def _vm_normalize(text):

    return (
        str(text)
        .lower()
        .strip()
        .strip("?.!,")
    )


class VoiceManagerPro(VoiceManager):

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
        "wake up"
    }

    EXIT_WORDS = {
        "exit",
        "quit",
        "stop",
        "goodbye",
        "bye luna",
        "see you later"
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

    SLEEP_TRIGGERS = {
        "go to sleep",
        "go to sleep luna",
        "sleep luna",
        "take a nap",
        "sleep"
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

    def __init__(
        self,
        wake_word_required=False,
        enable_barge_in=True,
    ):

        super().__init__()

        # -----------------------------
        # SESSION STATE
        # -----------------------------

        self.running = True

        self.awake = not bool(
            wake_word_required
        )

        self.wake_word_required = bool(
            wake_word_required
        )

        self.enable_barge_in = bool(
            enable_barge_in
        )

        self.muted = False

        self._session_start = (
            time.monotonic()
        )

        # -----------------------------
        # TYPED TEXT INJECTION
        # -----------------------------

        self._injected = queue.Queue()

        # -----------------------------
        # MEMORY + STATS
        # -----------------------------

        self.conversation_log = []

        self._last_response = ""

        self.stats = {
            "user_messages": 0,
            "luna_responses": 0,
            "fast_commands": 0,
            "repeats": 0,
            "barge_ins": 0,
            "errors": 0,
            "empty_responses": 0,
            "wakeups": 0,
            "sleeps": 0,
            "mutes": 0,
        }

        # -----------------------------
        # HOOKS (UI integration)
        # -----------------------------

        self.on_user_text = None

        self.on_response = None

        self.on_notice = None

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
                    "today's date",
                ],
                self._quick_date,
            ),
            (
                [
                    "battery",
                    "battery status",
                    "battery level",
                    "check battery",
                    "what's my battery level",
                    "what is my battery level",
                    "how much battery do i have",
                ],
                self._quick_battery,
            ),
            (
                [
                    "system health",
                    "system status",
                    "cpu status",
                    "how's my cpu",
                    "ram usage",
                    "performance",
                ],
                self._quick_health,
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
        # WRAP COMPONENTS
        # (original methods preserved
        #  and called through)
        # -----------------------------

        self._original_listen = (
            self.stt.listen
        )

        self.stt.listen = (
            self._wrapped_listen
        )

        self._original_chat = (
            self.luna.chat
        )

        self.luna.chat = (
            self._wrapped_chat
        )

        self._original_speak = (
            self.tts.speak
        )

        self.tts.speak = (
            self._wrapped_speak
        )

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

    def _quick_health(self):

        try:

            import psutil

            cpu = round(
                psutil.cpu_percent(
                    interval=0.5
                )
            )

            ram = round(
                psutil.virtual_memory()
                .percent
            )

            return (
                f"CPU is at {cpu} percent. "
                f"Memory is at {ram} percent."
            )

        except Exception:

            return (
                "I couldn't read the "
                "system health."
            )

    def _tap_volume(
        self,
        virtual_key,
        presses=6,
    ):

        try:

            import ctypes

            for _ in range(presses):

                ctypes.windll.user32.keybd_event(
                    virtual_key,
                    0,
                    0,
                    0,
                )

                ctypes.windll.user32.keybd_event(
                    virtual_key,
                    0,
                    2,
                    0,
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

            return (
                "Turning the volume down."
            )

        return (
            "Volume control is only "
            "available on Windows."
        )

    def _match_quick_command(
        self,
        normalized,
    ):

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
                            f"[LUNA] Quick command "
                            f"error: {error}"
                        )

                        return (
                            "That quick command "
                            "didn't work."
                        )

        return None

    def register_quick_command(
        self,
        phrases,
        handler,
    ):

        if isinstance(handler, str):

            text = handler

            handler = (
                lambda: text
            )

        self._custom_quick.append(
            (
                [
                    _vm_normalize(phrase)
                    for phrase in phrases
                ],
                handler,
            )
        )

    # ==================================================
    # WRAPPED LISTEN
    # (injection, wake word, mute, sleep)
    # ==================================================

    def _wrapped_listen(self):

        # 1) Typed text injected via
        #    submit_text() jumps the queue
        #    (and wakes LUNA if asleep).

        try:

            injected = (
                self._injected.get_nowait()
            )

            if injected:

                self.awake = True

                self._log_user(
                    injected
                )

                return injected

        except queue.Empty:

            pass

        # 2) Real microphone listen.

        heard = self._original_listen()

        if not self.running:

            return heard

        text = str(
            heard or ""
        ).strip()

        if not text:

            return heard

        normalized = _vm_normalize(
            text
        )

        # 3) Asleep — only wake words pass.

        if not self.awake:

            if self._is_wake_phrase(
                normalized
            ):

                self._wake_up()

            return ""

        # 4) Voice control phrases.

        if normalized in self.SLEEP_TRIGGERS:

            self._go_to_sleep()

            return ""

        if normalized in self.MUTE_TRIGGERS:

            self.set_muted(True)

            return ""

        if normalized in self.UNMUTE_TRIGGERS:

            self.set_muted(False)

            return ""

        # 5) Normal speech — log + pass through.
        #    ("repeat that", exit words and real
        #     questions all continue below.)

        self._log_user(text)

        return heard

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

    # ==================================================
    # WRAPPED CHAT (quick commands + repeat)
    # ==================================================

    def _wrapped_chat(
        self,
        text,
        *args,
        **kwargs,
    ):

        normalized = _vm_normalize(
            text
        )

        if (
            normalized
            in self.REPEAT_TRIGGERS
            and self._last_response
        ):

            self.stats[
                "repeats"
            ] += 1

            return self._last_response

        quick = self._match_quick_command(
            normalized
        )

        if quick is not None:

            self.stats[
                "fast_commands"
            ] += 1

            return quick

        return self._original_chat(
            text,
            *args,
            **kwargs,
        )

    # ==================================================
    # WRAPPED SPEAK (mute support)
    # ==================================================

    def _wrapped_speak(
        self,
        text,
        *args,
        **kwargs,
    ):

        if self.muted:

            print(
                f"[LUNA] 🔇 (muted) {text}"
            )

            return None

        return self._original_speak(
            text,
            *args,
            **kwargs,
        )

    def set_muted(self, muted):

        self.muted = bool(muted)

        self.stats["mutes"] += 1

        self._notice(
            "Muted — I'll reply in text only."
            if self.muted
            else "Unmuted — voice is back."
        )

    # ==================================================
    # SLEEP / WAKE
    # ==================================================

    def _go_to_sleep(self):

        if not self.awake:

            return

        self.awake = False

        self.stats["sleeps"] += 1

        self._notice(
            "Sleeping. Say 'hey LUNA' "
            "to wake me."
        )

    def _wake_up(self):

        self.awake = True

        self.stats["wakeups"] += 1

        self._notice(
            "I'm awake! What do you need?"
        )

    # ==================================================
    # LOGGING + HOOKS
    # ==================================================

    def _log_user(self, text):

        self.stats[
            "user_messages"
        ] += 1

        self.conversation_log.append(
            {
                "time": datetime.datetime
                .now()
                .strftime("%H:%M"),

                "role": "user",

                "text": str(text),
            }
        )

        self._trim_log()

        if self.on_user_text:

            try:

                self.on_user_text(
                    str(text)
                )

            except Exception:

                pass

    def _log_luna(self, text):

        self.conversation_log.append(
            {
                "time": datetime.datetime
                .now()
                .strftime("%H:%M"),

                "role": "luna",

                "text": str(text),
            }
        )

        self._trim_log()

    def _trim_log(self):

        if len(
            self.conversation_log
        ) > 500:

            self.conversation_log = (
                self.conversation_log[-500:]
            )

    def _notice(self, message):

        print(
            f"[LUNA] 💬 {message}"
        )

        if self.on_notice:

            try:

                self.on_notice(
                    str(message)
                )

            except Exception:

                pass

    # ==================================================
    # LANGUAGE HANDLING (FIX for Latin-script replies)
    # ==================================================

    def _contains_native_script(self, text):

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

    def _response_language(self, response):

        # Native script — trust the text itself.

        detected = (
            self.tts.detect_text_language(
                response
            )
        )

        if detected != "en":

            return detected

        # Latin script — use the language the
        # USER spoke when Whisper is confident.
        # (Fixes French/Spanish/German replies
        #  being read by the English voice.)

        stt_language = str(
            getattr(
                self.stt,
                "last_language",
                "unknown",
            )
            or "unknown"
        )

        probability = float(
            getattr(
                self.stt,
                "last_language_probability",
                0.0,
            )
            or 0.0
        )

        if (
            stt_language
            not in ("unknown", "en")
            and probability >= 0.65
        ):

            return stt_language

        return "en"

    # ==================================================
    # BARGE-IN WHILE SPEAKING
    # ==================================================

    def _make_interrupt_listener(self):

        try:

            from voice.interrupt_listener import (
                InterruptListener,
            )

        except ImportError:

            try:

                from interrupt_listener import (
                    InterruptListener,
                )

            except ImportError:

                return None

        try:

            return InterruptListener(
                self.tts
            )

        except Exception as error:

            print(
                f"⚠️ Barge-in listener "
                f"unavailable: {error}"
            )

            return None

    def _on_barge_in(self, text="stop"):

        self.stats[
            "barge_ins"
        ] += 1

        print(
            f"🛑 LUNA interrupted: {text}"
        )

    def _speak_with_barge_in(
        self,
        text,
        language=None,
    ):

        listener = None

        if self.enable_barge_in:

            listener = (
                self._make_interrupt_listener()
            )

            if listener is not None:

                if hasattr(
                    listener,
                    "on_stop_detected",
                ):

                    listener.on_stop_detected = (
                        self._on_barge_in
                    )

                try:

                    listener.start()

                except Exception:

                    listener = None

        try:

            return self.tts.speak(
                text,
                language=language,
            )

        finally:

            if listener is not None:

                try:

                    listener.stop()

                except Exception:

                    pass

    # ==================================================
    # RESPONSE DELIVERY
    # ==================================================

    def _deliver(self, response):

        self._last_response = str(
            response
        )

        self.stats[
            "luna_responses"
        ] += 1

        self._log_luna(response)

        if self.on_response:

            try:

                self.on_response(
                    str(response)
                )

            except Exception as error:

                print(
                    f"[LUNA] Response hook "
                    f"error: {error}"
                )

        language = (
            self._response_language(
                response
            )
        )

        self._speak_with_barge_in(
            response,
            language=language,
        )

    # ==================================================
    # SESSION LOOP (enhanced start)
    # ==================================================

    def start(self):

        self.running = True

        self._session_start = (
            time.monotonic()
        )

        # Original banner, then Pro extras.

        print("\n🌙 LUNA Voice Mode")
        print("=" * 50)
        print("Say 'exit' to stop.")
        print()

        if self.wake_word_required:

            self.awake = False

            print(
                "💤 Sleeping — say 'hey LUNA' "
                "to wake me."
            )

        print(
            "⚡ Instant commands: time · date · "
            "battery · system health · "
            "volume up/down"
        )

        print(
            "🔁 Say 'repeat that' to hear the "
            "last answer again."
        )

        if self.enable_barge_in:

            print(
                "🛑 Say 'stop' while LUNA speaks "
                "to interrupt her."
            )

        print()

        try:

            while self.running:

                try:

                    text = self.stt.listen()

                    if not self.running:

                        break

                    if not text:

                        continue

                    text = str(text).strip()

                    if not text:

                        continue

                    # FIX: punctuation-tolerant
                    # exit matching ("exit." works).

                    command = (
                        text.lower()
                        .strip()
                        .rstrip("?.!")
                    )

                    if command in self.EXIT_WORDS:

                        self.tts.speak(
                            "Goodbye. See you later."
                        )

                        break

                    print(
                        "\n🧠 LUNA is thinking..."
                    )

                    try:

                        response = (
                            self.luna.chat(
                                text,
                                model="groq",
                            )
                        )

                        if response:

                            response = str(
                                response
                            ).strip()

                            if response:

                                self._deliver(
                                    response
                                )

                                continue

                        # FIX: empty response —
                        # speak instead of silence.

                        self.stats[
                            "empty_responses"
                        ] += 1

                        self._deliver(
                            "I didn't receive a "
                            "response. Could you "
                            "say that again?"
                        )

                    except Exception as error:

                        print(
                            f"❌ AI error: {error}"
                        )

                        self.stats[
                            "errors"
                        ] += 1

                        self.tts.speak(
                            "Sorry, something "
                            "went wrong."
                        )

                except KeyboardInterrupt:

                    raise

                except Exception as error:

                    # FIX: mic errors no longer
                    # kill the session.

                    print(
                        f"❌ Voice error: {error}"
                    )

                    self.stats[
                        "errors"
                    ] += 1

                    time.sleep(0.5)

        except KeyboardInterrupt:

            # FIX: Ctrl+C exits gracefully
            # instead of a raw traceback.

            print(
                "\n👋 Session interrupted — goodbye!"
            )

        finally:

            self._shutdown()

    # ==================================================
    # SHUTDOWN
    # ==================================================

    def _shutdown(self):

        self.running = False

        try:

            self.tts.stop()

        except Exception:

            pass

        # FIX: the original never shut the
        # agent down — resources leaked.

        shutdown = getattr(
            self.luna,
            "shutdown",
            None,
        )

        if callable(shutdown):

            try:

                shutdown()

            except Exception as error:

                print(
                    f"[LUNA] Agent shutdown "
                    f"warning: {error}"
                )

        self._print_summary()

    def _print_summary(self):

        seconds = int(
            time.monotonic()
            - self._session_start
        )

        minutes = seconds // 60

        print()
        print("=" * 50)
        print("📊 Session summary")
        print(
            f"   Duration: "
            f"{minutes}m {seconds % 60}s"
        )
        print(
            f"   Your messages: "
            f"{self.stats['user_messages']}"
        )
        print(
            f"   LUNA replies: "
            f"{self.stats['luna_responses']}"
        )
        print(
            f"   Instant commands: "
            f"{self.stats['fast_commands']}"
        )
        print(
            f"   Repeats: "
            f"{self.stats['repeats']}"
        )
        print(
            f"   Barge-ins: "
            f"{self.stats['barge_ins']}"
        )
        print(
            f"   Errors: "
            f"{self.stats['errors']}"
        )
        print("=" * 50)

    # ==================================================
    # PUBLIC API
    # ==================================================

    def stop(self):

        # Thread-safe: call from anywhere
        # to end the session.

        self.running = False

        try:

            self.tts.stop()

        except Exception:

            pass

    def submit_text(self, text):

        # Typed input rides the SAME pipeline
        # as voice (quick commands, language
        # handling, TTS, logging).

        text = str(
            text or ""
        ).strip()

        if text:

            self._injected.put(text)

    def get_stats(self):

        stats = dict(self.stats)

        seconds = int(
            time.monotonic()
            - self._session_start
        )

        minutes = seconds // 60

        stats["session_duration"] = (
            f"{minutes}m {seconds % 60}s"
        )

        stats["awake"] = self.awake

        stats["muted"] = self.muted

        return stats

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
                    "luna_console_"
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
# Anything that imports VoiceManager from this file now gets
# the extended version automatically (VoiceManager() with no
# arguments keeps the original conversational behavior —
# just more resilient and with more abilities).
# Delete the next line to keep using the original.
# ------------------------------------------------------------

VoiceManager = VoiceManagerPro


# ============================================================
# QUICK TEST (uncomment to try)
# ============================================================
#
# if __name__ == "__main__":
#
#     manager = VoiceManager()
#
#     # Optional Pro configuration:
#     # manager = VoiceManager(wake_word_required=True)
#     # manager.register_quick_command(
#     #     ["joke"], "Why did the AI cross the road?"
#     # )
#
#     manager.start()
#
#     # After the session:
#     # manager.export_session()
#     # print(manager.get_stats())