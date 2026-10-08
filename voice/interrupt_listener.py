import threading

import speech_recognition as sr


class InterruptListener:

    def __init__(
        self,
        tts
    ):

        self.tts = tts

        self.running = False

        self.thread = None

        self.recognizer = sr.Recognizer()

        self.recognizer.energy_threshold = 350

        self.recognizer.dynamic_energy_threshold = True

        self.recognizer.pause_threshold = 0.4

        self.recognizer.phrase_threshold = 0.2

        self.recognizer.non_speaking_duration = 0.2

        self.stop_words = {
            "stop",
            "luna stop",
            "stop luna",
            "cancel",
            "cancel that",
            "be quiet",
        }

    # ==================================================
    # START
    # ==================================================

    def start(self):

        if self.running:

            return

        self.running = True

        self.thread = threading.Thread(
            target=self._listen_loop,
            daemon=True
        )

        self.thread.start()

    # ==================================================
    # STOP LISTENER
    # ==================================================

    def stop(self):

        self.running = False

    # ==================================================
    # LISTEN LOOP
    # ==================================================

    def _listen_loop(self):

        while self.running:

            try:

                with sr.Microphone() as source:

                    try:

                        audio = (
                            self.recognizer.listen(
                                source,
                                timeout=1,
                                phrase_time_limit=2
                            )
                        )

                    except sr.WaitTimeoutError:

                        continue

                if not self.running:

                    break

                try:

                    text = (
                        self.recognizer
                        .recognize_google(
                            audio
                        )
                        .lower()
                        .strip()
                    )

                except sr.UnknownValueError:

                    continue

                except sr.RequestError:

                    continue

                if not text:

                    continue

                print(
                    f"🛑 Interrupt listener: {text}"
                )

                # --------------------------------------
                # Exact / strong stop detection
                # --------------------------------------

                if self._is_stop_command(
                    text
                ):

                    self.tts.stop()

                    self.running = False

                    break

            except Exception as error:

                if self.running:

                    print(
                        f"⚠️ Interrupt listener: "
                        f"{error}"
                    )

    # ==================================================
    # STOP COMMAND
    # ==================================================

    def _is_stop_command(
        self,
        text
    ):

        if text in self.stop_words:

            return True

        words = text.split()

        if len(words) <= 4:

            if "stop" in words:

                return True

            if "cancel" in words:

                return True

        return False


# ============================================================
# ============================================================
#
#   🌙 LUNA INTERRUPT LISTENER PRO — EXTENSIONS (APPEND ONLY)
#
#   The original InterruptListener above is 100% unchanged.
#   InterruptListenerPro reuses the base recognizer and the
#   base _is_stop_command, and replaces only the loop.
#
#   FIXES
#     • One-shot listener — the original set running=False
#       after the first interrupt, so it could NEVER stop
#       a second speech. Pro adds a keep_alive mode.
#     • Restart race — start() after stop() could spawn a
#       second thread while the old one was still winding
#       down (two listeners fighting over the mic). Pro
#       checks thread liveness before starting.
#     • stop() never joined the thread — the mic could stay
#       captured for up to ~1s after "stopping". Pro joins.
#     • Error busy-loop — if the mic is busy/unavailable,
#       the original spun in a tight exception loop printing
#       warnings nonstop. Pro backs off exponentially.
#     • Silent offline failure — Google requests fail with
#       RequestError when offline and everything is dropped.
#       Pro falls back to local Sphinx recognition.
#     • False positives — Google mishears "stop" inside
#       short phrases ("let's top up"). Pro can re-verify
#       with a local Whisper transcriber before stopping.
#
#   ADDITIONS
#     • Whisper verification hook (inject stt._transcribe_barge_in)
#     • on_stop_detected callback (generation-guard integration)
#     • Cooldown between interrupts (no double-triggers)
#     • Microphone device selection
#     • Configurable listen timings (with validation)
#     • interrupt_now() manual trigger + stats + context manager
#
# ============================================================
# ============================================================

import time

import numpy as np


class InterruptListenerPro(InterruptListener):

    def __init__(
        self,
        tts,
        verify_transcriber=None,
        keep_alive=False,
    ):

        super().__init__(tts)

        # -----------------------------
        # BEHAVIOUR
        # keep_alive=False preserves the
        # original one-shot behaviour.
        # -----------------------------

        self.keep_alive = bool(
            keep_alive
        )

        self.cooldown = 1.0

        self._last_interrupt = 0.0

        # -----------------------------
        # WHISPER VERIFICATION
        # Pass stt._transcribe_barge_in
        # to double-check Google's answer
        # locally before stopping TTS.
        # -----------------------------

        self.verify_transcriber = (
            verify_transcriber
        )

        # -----------------------------
        # GENERATION-GUARD HOOK
        # -----------------------------

        self.on_stop_detected = None

        # -----------------------------
        # TUNABLE TIMINGS
        # (defaults match the original)
        # -----------------------------

        self.listen_timeout = 1.0

        self.phrase_time_limit = 2.0

        self.device_index = None

        self.offline_fallback = True

        # -----------------------------
        # STATS
        # -----------------------------

        self._stats = {
            "listen_cycles": 0,
            "recognitions": 0,
            "stop_commands": 0,
            "false_positives": 0,
            "offline_used": 0,
            "errors": 0,
        }

    # ==================================================
    # START (restart-safe)
    # ==================================================

    def start(self):

        thread = self.thread

        if (
            thread is not None
            and thread.is_alive()
        ):

            return

        self.running = True

        self.thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
        )

        self.thread.start()

    # ==================================================
    # STOP (joins the thread)
    # ==================================================

    def stop(self):

        super().stop()

        thread = self.thread

        if (
            thread is not None
            and thread.is_alive()
        ):

            thread.join(
                timeout=3.0
            )

        self.thread = None

    def is_active(self):

        thread = self.thread

        return (
            self.running
            and thread is not None
            and thread.is_alive()
        )

    # ==================================================
    # CONFIGURATION
    # ==================================================

    def set_microphone(self, device_index):

        self.device_index = device_index

    def set_timing(
        self,
        pause_threshold=None,
        non_speaking_duration=None,
        listen_timeout=None,
        phrase_time_limit=None,
    ):

        # speech_recognition requires
        # non_speaking_duration <=
        # pause_threshold — clamp to
        # respect that constraint.

        if pause_threshold is not None:

            pause = max(
                0.1,
                float(pause_threshold),
            )

            current_gap = (
                non_speaking_duration
                if non_speaking_duration
                is not None
                else self.recognizer
                .non_speaking_duration
            )

            self.recognizer.pause_threshold = pause

            self.recognizer.non_speaking_duration = min(
                current_gap,
                pause,
            )

        if non_speaking_duration is not None:

            gap = max(
                0.05,
                float(non_speaking_duration),
            )

            self.recognizer.non_speaking_duration = min(
                gap,
                self.recognizer.pause_threshold,
            )

        if listen_timeout is not None:

            self.listen_timeout = max(
                0.3,
                float(listen_timeout),
            )

        if phrase_time_limit is not None:

            self.phrase_time_limit = max(
                0.5,
                float(phrase_time_limit),
            )

    def add_stop_word(self, word):

        word = (
            str(word)
            .lower()
            .strip()
        )

        if word:

            self.stop_words.add(
                word
            )

    # ==================================================
    # MANUAL TRIGGER
    # ==================================================

    def interrupt_now(self):

        self._trigger_stop(
            "manual interrupt"
        )

    # ==================================================
    # AUDIO CONVERSION (for Whisper verification)
    # ==================================================

    def _audio_to_float32(self, audio):

        try:

            raw = audio.get_raw_data(
                convert_rate=16000,
                convert_width=2,
            )

            samples = np.frombuffer(
                raw,
                dtype=np.int16,
            )

            return (
                samples.astype(np.float32)
                / 32768.0
            )

        except Exception:

            return None

    def _verify(self, audio):

        try:

            samples = (
                self._audio_to_float32(
                    audio
                )
            )

            if (
                samples is None
                or len(samples) < 1600
            ):

                # too short to verify —
                # trust the cloud result

                return True

            verified = (
                self.verify_transcriber(
                    samples
                )
            )

            if not verified:

                return False

            return (
                self._is_stop_command(
                    str(verified)
                    .lower()
                    .strip()
                )
            )

        except Exception as error:

            print(
                f"⚠️ Interrupt verification "
                f"error: {error}"
            )

            # on verification failure,
            # trust the cloud result

            return True

    # ==================================================
    # OFFLINE RECOGNITION
    # ==================================================

    def _offline_recognize(self, audio):

        if not self.offline_fallback:

            return ""

        try:

            text = (
                self.recognizer
                .recognize_sphinx(audio)
                .lower()
                .strip()
            )

            self._stats[
                "offline_used"
            ] += 1

            return text

        except Exception:

            return ""

    # ==================================================
    # TRIGGER
    # ==================================================

    def _trigger_stop(self, text):

        now = time.monotonic()

        if (
            now - self._last_interrupt
            < self.cooldown
        ):

            return

        self._last_interrupt = now

        self._stats[
            "stop_commands"
        ] += 1

        print(
            f"🛑 Interrupt listener: {text}"
        )

        if self.on_stop_detected:

            try:

                self.on_stop_detected(
                    text
                )

            except Exception as error:

                print(
                    f"⚠️ Interrupt callback "
                    f"error: {error}"
                )

        try:

            self.tts.stop()

        except Exception as error:

            print(
                f"⚠️ TTS stop error: {error}"
            )

        if not self.keep_alive:

            self.running = False

    # ==================================================
    # LISTEN LOOP (Pro)
    # ==================================================

    def _listen_loop(self):

        consecutive_errors = 0

        while self.running:

            try:

                self._stats[
                    "listen_cycles"
                ] += 1

                with sr.Microphone(
                    device_index=self.device_index
                ) as source:

                    try:

                        audio = (
                            self.recognizer.listen(
                                source,
                                timeout=self.listen_timeout,
                                phrase_time_limit=self.phrase_time_limit,
                            )
                        )

                    except sr.WaitTimeoutError:

                        continue

                if not self.running:

                    break

                try:

                    text = (
                        self.recognizer
                        .recognize_google(
                            audio
                        )
                        .lower()
                        .strip()
                    )

                except sr.UnknownValueError:

                    continue

                except sr.RequestError:

                    # offline — try local engine

                    text = (
                        self._offline_recognize(
                            audio
                        )
                    )

                consecutive_errors = 0

                if not text:

                    continue

                self._stats[
                    "recognitions"
                ] += 1

                print(
                    f"🛑 Interrupt listener: {text}"
                )

                # --------------------------------------
                # OPTIONAL WHISPER VERIFICATION
                # --------------------------------------

                if (
                    self.verify_transcriber
                    is not None
                    and not self._verify(
                        audio
                    )
                ):

                    self._stats[
                        "false_positives"
                    ] += 1

                    continue

                # --------------------------------------
                # STOP DETECTION (base logic)
                # --------------------------------------

                if self._is_stop_command(
                    text
                ):

                    self._trigger_stop(
                        text
                    )

                    if not self.running:

                        break

            except Exception as error:

                if not self.running:

                    break

                self._stats[
                    "errors"
                ] += 1

                consecutive_errors += 1

                print(
                    f"⚠️ Interrupt listener: "
                    f"{error}"
                )

                # exponential backoff —
                # never busy-loop on a
                # broken microphone

                time.sleep(
                    min(
                        0.5
                        * (
                            2
                            ** consecutive_errors
                        ),
                        5.0,
                    )
                )

    # ==================================================
    # STATS
    # ==================================================

    def get_stats(self):

        stats = dict(self._stats)

        stats["active"] = (
            self.is_active()
        )

        stats["keep_alive"] = (
            self.keep_alive
        )

        stats["verified"] = (
            self.verify_transcriber
            is not None
        )

        return stats

    # ==================================================
    # CONTEXT MANAGER
    # ==================================================

    def __enter__(self):

        self.start()

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):

        self.stop()

        return False


# ------------------------------------------------------------
# DROP-IN UPGRADE
# Anything that imports InterruptListener from this file now
# gets the extended version automatically (same API — the
# two-argument constructor InterruptListener(tts) is
# unchanged and preserves the original one-shot behaviour).
# Delete the next line to keep using the original.
# ------------------------------------------------------------

InterruptListener = InterruptListenerPro


# ============================================================
# QUICK TEST (uncomment to try)
# ============================================================
#
# if __name__ == "__main__":
#
#     import time
#
#     class FakeTTS:
#         def stop(self):
#             print(">>> TTS STOPPED")
#
#     listener = InterruptListener(
#         FakeTTS(),
#         keep_alive=True,       # survives the first interrupt
#     )
#
#     listener.add_stop_word("shut up")
#     listener.set_timing(listen_timeout=1.5)
#
#     with listener:
#         time.sleep(30)   # say "stop" to interrupt, Ctrl+C to exit
#
#     print(listener.get_stats())