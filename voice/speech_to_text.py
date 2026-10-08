import queue
import time
from typing import Optional

import numpy as np
import sounddevice as sd

from faster_whisper import WhisperModel


class SpeechToText:

    def __init__(self):

        # ====================================================
        # LOAD MODEL
        # ====================================================

        print(
            "🌙 Loading multilingual LUNA speech model..."
        )

        self.model = WhisperModel(
            "tiny",
            device="cpu",
            compute_type="int8",
        )

        print(
            "✅ Multilingual speech model ready."
        )

        # ====================================================
        # AUDIO
        # ====================================================

        self.sample_rate = 16000

        self.channels = 1

        self.block_duration = 0.20

        self.block_size = int(
            self.sample_rate
            * self.block_duration
        )

        # ====================================================
        # RECORDING
        # ====================================================

        self.energy_threshold = 0.010

        self.silence_duration = 0.70

        self.max_recording_time = 10.0

        self.min_recording_time = 0.25

        # ====================================================
        # LANGUAGE
        # ====================================================

        self.last_language = "unknown"

        self.last_language_probability = 0.0

    # ========================================================
    # RECORD AUDIO
    # ========================================================

    def _record_audio(self):

        audio_queue = queue.Queue()

        recording = []

        speech_started = False

        start_time = None

        last_voice_time = None

        def callback(
            indata,
            frames,
            time_info,
            status,
        ):

            if status:

                print(
                    f"🎙️ Audio status: {status}"
                )

            audio_queue.put(
                indata[:, 0].copy()
            )

        try:

            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                blocksize=self.block_size,
                callback=callback,
            ):

                print(
                    "\n🎙️ Listening..."
                )

                wait_start = time.time()

                while True:

                    try:

                        audio = audio_queue.get(
                            timeout=0.5
                        )

                    except queue.Empty:

                        if (
                            time.time()
                            - wait_start
                            > 8
                        ):

                            return None

                        continue

                    recording.append(
                        audio
                    )

                    now = time.time()

                    rms = float(
                        np.sqrt(
                            np.mean(
                                audio * audio
                            )
                        )
                    )

                    # ----------------------------------------
                    # SPEECH START
                    # ----------------------------------------

                    if (
                        rms
                        >= self.energy_threshold
                    ):

                        if not speech_started:

                            speech_started = True

                            start_time = now

                            print(
                                "🎤 Speech detected..."
                            )

                        last_voice_time = now

                    # ----------------------------------------
                    # SPEECH END
                    # ----------------------------------------

                    if speech_started:

                        speech_time = (
                            now - start_time
                        )

                        silence_time = (
                            now - last_voice_time
                            if last_voice_time
                            else 0
                        )

                        if (
                            speech_time
                            >= self.min_recording_time
                            and silence_time
                            >= self.silence_duration
                        ):

                            break

                        if (
                            speech_time
                            >= self.max_recording_time
                        ):

                            break

                if not recording:

                    return None

                return np.concatenate(
                    recording
                ).astype(
                    np.float32
                )

        except Exception as error:

            print(
                f"❌ Microphone error: {error}"
            )

            return None

    # ========================================================
    # TRANSCRIBE + DETECT LANGUAGE
    # ========================================================

    def _transcribe(
        self,
        audio,
    ):

        try:

            segments, info = (
                self.model.transcribe(

                    audio,

                    # None = automatic language detection
                    language=None,

                    beam_size=1,

                    best_of=1,

                    temperature=0,

                    vad_filter=True,

                    vad_parameters={
                        "min_silence_duration_ms": 450
                    },

                    condition_on_previous_text=False,
                )
            )

            # ----------------------------------------
            # LANGUAGE
            # ----------------------------------------

            detected_language = (
                getattr(
                    info,
                    "language",
                    None
                )
                or "unknown"
            )

            language_probability = float(
                getattr(
                    info,
                    "language_probability",
                    0.0
                )
                or 0.0
            )

            self.last_language = (
                detected_language
            )

            self.last_language_probability = (
                language_probability
            )

            # ----------------------------------------
            # TEXT
            # ----------------------------------------

            parts = []

            for segment in segments:

                text = (
                    segment.text
                    .strip()
                )

                if text:

                    parts.append(
                        text
                    )

            result = " ".join(
                parts
            ).strip()

            return result

        except Exception as error:

            print(
                f"❌ Whisper error: {error}"
            )

            self.last_language = "unknown"

            self.last_language_probability = 0.0

            return None

    # ========================================================
    # TRANSCRIBE FOR BARGE-IN  (short English stop commands)
    # ========================================================

    def _transcribe_barge_in(
        self,
        audio: "np.ndarray",
    ) -> "Optional[str]":
        """Specialised transcription for barge-in detection.

        Key differences from ``_transcribe``:
        - Language is **forced to English** so that Whisper does not
          waste time on language detection and does not hallucinate
          non-English tokens from background noise.
        - ``beam_size=5`` / ``best_of=5`` for better accuracy on the
          very short single-word utterances typical of stop commands.
        - ``temperature=0`` with no fallback eliminates the random
          "creativity" that causes repetition hallucinations.
        - Tighter VAD silence window (200 ms) to avoid over-capturing.
        """
        try:

            segments, _info = self.model.transcribe(

                audio,

                # Force English — barge-in commands are always English.
                language="en",

                # Higher beam/best_of for short-utterance accuracy.
                beam_size=5,

                best_of=5,

                # No temperature fallback — prevents repetition loops.
                temperature=0,

                vad_filter=True,

                vad_parameters={
                    "min_silence_duration_ms": 200,
                },

                condition_on_previous_text=False,
            )

            parts = []

            for segment in segments:

                text = segment.text.strip()

                if text:
                    parts.append(text)

            return " ".join(parts).strip() or None

        except Exception as error:

            print(
                f"❌ Barge-in transcription error: {error}"
            )

            return None

    # ========================================================
    # BARGE-IN COMMAND TRANSCRIPTION
    # ========================================================

    def _transcribe_barge_in(self, audio):
        """Fast, English-focused decoding for STOP/cancel commands.

        Main LUNA STT remains multilingual. Barge-in commands are intentionally
        decoded as English because the interruption phrases are English and
        this avoids language-detection drift on very short utterances.
        """
        try:
            segments, _info = self.model.transcribe(
                audio,
                language="en",
                beam_size=3,
                best_of=3,
                temperature=0,
                vad_filter=False,
                condition_on_previous_text=False,
                without_timestamps=True,
                initial_prompt=(
                    "stop, stop Luna, stop speaking, stop it, cancel, "
                    "cancel Luna, be quiet, quiet, that's enough, enough"
                ),
                no_speech_threshold=0.20,
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0,
            )

            parts = []
            for segment in segments:
                text = str(getattr(segment, "text", "") or "").strip()
                if text:
                    parts.append(text)

            return " ".join(parts).strip() or None

        except Exception as error:
            print(f"❌ Barge-in Whisper error: {error}")
            return None

    # ========================================================
    # LISTEN
    # ========================================================

    def listen(self):

        audio = self._record_audio()

        if audio is None:

            return None

        # ----------------------------------------
        # CHECK AUDIO
        # ----------------------------------------

        rms = float(
            np.sqrt(
                np.mean(
                    audio * audio
                )
            )
        )

        if rms < (
            self.energy_threshold / 2
        ):

            print(
                "❌ No meaningful speech detected."
            )

            return None

        print(
            "🧠 Transcribing..."
        )

        text = self._transcribe(
            audio
        )

        if not text:

            print(
                "❌ I couldn't understand that."
            )

            return None

        print(
            f"🌐 Language: "
            f"{self.last_language} "
            f"({self.last_language_probability:.2f})"
        )

        print(
            f"📝 You said: {text}"
        )

        return text


# ============================================================
# ============================================================
#
#   🌙 LUNA SPEECH-TO-TEXT PRO — EXTENSIONS (APPEND ONLY)
#
#   The original SpeechToText above is 100% unchanged —
#   including BOTH duplicate _transcribe_barge_in
#   definitions (a real bug — the second silently
#   replaced the first, making it dead code).
#
#   FIXES
#     • _transcribe_barge_in unified into ONE authoritative
#       method (behaviour of the definition that was
#       actually running is preserved exactly)
#     • Whisper-tiny hallucination filter — silence no
#       longer becomes "Thank you." / "you you you"
#       phantom commands sent to the AI
#     • Hardcoded 8-second wait timeout → configurable
#
#   ADDITIONS
#     • on_level / on_speech_start / on_speech_end hooks
#       (real mic waveform feeds the UI audio ring)
#     • calibrate() — measures room noise, sets threshold
#     • Opt-in adaptive noise-floor threshold
#     • list_microphones() / set_microphone() / device
#     • pause_listening() / resume_listening()
#     • transcribe_detailed() — language + confidence
#     • transcribe_file() — test .wav files directly
#     • is_stop_command() — shared stop-phrase checker
#     • get_stats() — session diagnostics
#
# ============================================================
# ============================================================

import wave


class SpeechToTextPro(SpeechToText):

    # ==================================================
    # HALLUCINATION TABLE
    # Only drops a transcript if the ENTIRE result
    # matches — real commands are never affected.
    # ==================================================

    HALLUCINATION_PHRASES = {
        "thank you",
        "thanks for watching",
        "subscribe",
        "bye",
        "you",
        "the",
        "i'm sorry",
    }

    STOP_COMMAND_PHRASES = {
        "stop",
        "stop luna",
        "stop speaking",
        "stop it",
        "cancel",
        "cancel luna",
        "be quiet",
        "quiet",
        "that's enough",
        "enough",
        "shut up",
    }

    def __init__(self):

        super().__init__()

        # -----------------------------
        # DEVICE
        # -----------------------------

        self.device = None

        # -----------------------------
        # LIVE HOOKS
        # -----------------------------

        self.on_level = None

        self.on_speech_start = None

        self.on_speech_end = None

        self.last_level = 0.0

        self.level_scale = 10.0

        # -----------------------------
        # TUNING
        # -----------------------------

        self.wait_timeout = 8.0

        self.auto_threshold = False

        self.noise_floor = None

        # -----------------------------
        # TEXT CLEANUP
        # -----------------------------

        self.hallucination_filter = True

        # -----------------------------
        # STATE
        # -----------------------------

        self._paused = False

        # -----------------------------
        # STATS
        # -----------------------------

        self._stats = {
            "listen_sessions": 0,
            "speech_captures": 0,
            "transcriptions": 0,
            "empty_results": 0,
            "filtered_hallucinations": 0,
            "total_listen_seconds": 0.0,
        }

        # -----------------------------
        # WRAP TRANSCRIBE
        # (original method preserved)
        # -----------------------------

        self._base_transcribe = (
            self._transcribe
        )

        self._transcribe = (
            self._wrapped_transcribe
        )

    # ==================================================
    # RECORD AUDIO (original loop + live hooks)
    # ==================================================

    def _record_audio(self):

        if self._paused:

            time.sleep(0.1)

            return None

        self._stats["listen_sessions"] += 1

        audio_queue = queue.Queue()

        recording = []

        speech_started = False

        start_time = None

        last_voice_time = None

        noise_levels = []

        started_at = time.time()

        def callback(
            indata,
            frames,
            time_info,
            status,
        ):

            if status:

                print(
                    f"🎙️ Audio status: {status}"
                )

            audio_queue.put(
                indata[:, 0].copy()
            )

        try:

            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                blocksize=self.block_size,
                callback=callback,
                device=self.device,
            ):

                print(
                    "\n🎙️ Listening..."
                )

                wait_start = time.time()

                while True:

                    try:

                        audio = audio_queue.get(
                            timeout=0.5
                        )

                    except queue.Empty:

                        if (
                            time.time()
                            - wait_start
                            > self.wait_timeout
                        ):

                            return None

                        continue

                    recording.append(
                        audio
                    )

                    now = time.time()

                    rms = float(
                        np.sqrt(
                            np.mean(
                                audio * audio
                            )
                        )
                    )

                    # ==================================
                    # NEW: LIVE LEVEL HOOK
                    # ==================================

                    self.last_level = rms

                    if self.on_level:

                        try:

                            self.on_level(
                                max(
                                    0.0,
                                    min(
                                        1.0,
                                        rms
                                        * self.level_scale,
                                    ),
                                )
                            )

                        except Exception:

                            pass

                    # ==================================
                    # NEW: NOISE FLOOR ADAPTATION
                    # (opt-in via auto_threshold)
                    # ==================================

                    if (
                        self.auto_threshold
                        and not speech_started
                    ):

                        noise_levels.append(
                            rms
                        )

                        if (
                            len(noise_levels)
                            >= 15
                        ):

                            floor = float(
                                np.median(
                                    noise_levels
                                )
                            )

                            self.noise_floor = (
                                floor
                            )

                            self.energy_threshold = max(
                                0.006,
                                min(
                                    0.05,
                                    floor * 2.5,
                                ),
                            )

                            noise_levels = []

                    # ----------------------------------------
                    # SPEECH START (original logic)
                    # ----------------------------------------

                    if (
                        rms
                        >= self.energy_threshold
                    ):

                        if not speech_started:

                            speech_started = True

                            start_time = now

                            print(
                                "🎤 Speech detected..."
                            )

                            if self.on_speech_start:

                                try:

                                    self.on_speech_start()

                                except Exception:

                                    pass

                        last_voice_time = now

                    # ----------------------------------------
                    # SPEECH END (original logic)
                    # ----------------------------------------

                    if speech_started:

                        speech_time = (
                            now - start_time
                        )

                        silence_time = (
                            now - last_voice_time
                            if last_voice_time
                            else 0
                        )

                        if (
                            speech_time
                            >= self.min_recording_time
                            and silence_time
                            >= self.silence_duration
                        ):

                            break

                        if (
                            speech_time
                            >= self.max_recording_time
                        ):

                            break

                if not recording:

                    return None

                # ==================================
                # NEW: SPEECH END HOOK + STATS
                # ==================================

                self._stats[
                    "speech_captures"
                ] += 1

                self._stats[
                    "total_listen_seconds"
                ] += (
                    time.time() - started_at
                )

                if (
                    self.on_speech_end
                    and start_time
                ):

                    try:

                        self.on_speech_end(
                            time.time() - start_time
                        )

                    except Exception:

                        pass

                return np.concatenate(
                    recording
                ).astype(
                    np.float32
                )

        except Exception as error:

            print(
                f"❌ Microphone error: {error}"
            )

            return None

    # ==================================================
    # WRAPPED TRANSCRIBE (filter + stats)
    # ==================================================

    def _wrapped_transcribe(self, audio):

        self._stats["transcriptions"] += 1

        result = self._base_transcribe(
            audio
        )

        if not result:

            self._stats[
                "empty_results"
            ] += 1

            return result

        cleaned = self._clean_text(
            str(result)
        )

        if not cleaned:

            self._stats[
                "filtered_hallucinations"
            ] += 1

            print(
                "🧹 Filtered Whisper "
                "hallucination from silence."
            )

            return None

        return cleaned

    def _clean_text(self, text):

        cleaned = " ".join(
            str(text).split()
        )

        if not cleaned:

            return None

        # pure punctuation → nothing

        if set(cleaned) <= set(".,!?;: "):

            return None

        if not self.hallucination_filter:

            return cleaned

        # exact whole-transcript hallucinations

        probe = cleaned.lower().strip("?.!,")

        if probe in self.HALLUCINATION_PHRASES:

            return None

        # "the the the the" loops

        words = cleaned.split()

        if (
            len(words) >= 3
            and len(
                set(
                    word.lower()
                    for word in words
                )
            )
            == 1
        ):

            return None

        # collapse 3+ immediate repeats

        deduped = []

        for word in words:

            if (
                len(deduped) >= 2
                and word.lower()
                == deduped[-1].lower()
                == deduped[-2].lower()
            ):

                continue

            deduped.append(word)

        cleaned = " ".join(deduped)

        return cleaned or None

    def add_hallucination(self, phrase):

        self.HALLUCINATION_PHRASES.add(
            str(phrase)
            .lower()
            .strip("?.!,")
        )

    # ==================================================
    # BARGE-IN — SINGLE UNIFIED VERSION
    # (resolves the duplicate-definition bug; behaviour
    #  of the definition that was actually running is
    #  preserved exactly)
    # ==================================================

    def _transcribe_barge_in(self, audio):

        try:

            segments, _info = (
                self.model.transcribe(
                    audio,
                    language="en",
                    beam_size=3,
                    best_of=3,
                    temperature=0,
                    vad_filter=False,
                    condition_on_previous_text=False,
                    without_timestamps=True,
                    initial_prompt=(
                        "stop, stop Luna, stop speaking, "
                        "stop it, cancel, cancel Luna, "
                        "be quiet, quiet, that's enough, "
                        "enough"
                    ),
                    no_speech_threshold=0.20,
                    compression_ratio_threshold=2.4,
                    log_prob_threshold=-1.0,
                )
            )

            parts = []

            for segment in segments:

                text = str(
                    getattr(
                        segment,
                        "text",
                        "",
                    )
                    or ""
                ).strip()

                if text:

                    parts.append(text)

            return (
                " ".join(parts).strip()
                or None
            )

        except Exception as error:

            print(
                f"❌ Barge-in Whisper error: {error}"
            )

            return None

    @classmethod
    def is_stop_command(cls, text):

        if not text:

            return False

        normalized = (
            str(text)
            .lower()
            .strip()
            .rstrip("?.!,")
        )

        return (
            normalized
            in cls.STOP_COMMAND_PHRASES
        )

    # ==================================================
    # CALIBRATION
    # ==================================================

    def calibrate(self, duration=1.5):

        frames = []

        def callback(
            indata,
            frames_count,
            time_info,
            status,
        ):

            frames.append(
                indata[:, 0].copy()
            )

        try:

            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                blocksize=self.block_size,
                callback=callback,
                device=self.device,
            ):

                print(
                    "🎚️ Calibrating — "
                    "please stay quiet..."
                )

                time.sleep(
                    max(0.3, float(duration))
                )

        except Exception as error:

            print(
                f"❌ Calibration error: {error}"
            )

            return None

        if not frames:

            return None

        levels = [
            float(
                np.sqrt(
                    np.mean(
                        frame * frame
                    )
                )
            )
            for frame in frames
        ]

        floor = float(
            np.median(levels)
        )

        self.noise_floor = floor

        self.energy_threshold = max(
            0.006,
            min(0.05, floor * 2.5),
        )

        print(
            f"🎚️ Noise floor {floor:.4f} → "
            f"threshold {self.energy_threshold:.4f}"
        )

        return self.energy_threshold

    # ==================================================
    # MICROPHONE SELECTION
    # ==================================================

    @staticmethod
    def list_microphones():

        devices = []

        try:

            default_input = (
                sd.default.device[0]
            )

            for index, info in enumerate(
                sd.query_devices()
            ):

                channels = int(
                    info.get(
                        "max_input_channels",
                        0,
                    )
                )

                if channels <= 0:

                    continue

                devices.append(
                    {
                        "index": index,
                        "name": str(
                            info.get(
                                "name",
                                "",
                            )
                        ),
                        "channels": channels,
                        "default": (
                            index
                            == default_input
                        ),
                    }
                )

        except Exception as error:

            print(
                f"❌ Microphone query error: {error}"
            )

        return devices

    def set_microphone(self, device):

        if isinstance(device, int):

            self.device = device

            return (
                f"Microphone set to "
                f"device index {device}."
            )

        if isinstance(device, str):

            target = (
                device.lower().strip()
            )

            for info in (
                self.list_microphones()
            ):

                if target in info[
                    "name"
                ].lower():

                    self.device = info[
                        "index"
                    ]

                    return (
                        f"Microphone set to "
                        f"{info['name']}."
                    )

            return (
                f"I couldn't find a microphone "
                f"matching '{device}'."
            )

        return "Invalid microphone selection."

    # ==================================================
    # PAUSE / RESUME
    # ==================================================

    def pause_listening(self):

        self._paused = True

        print("🎙️ Microphone paused.")

    def resume_listening(self):

        self._paused = False

        print("🎙️ Microphone resumed.")

    def is_paused(self):

        return self._paused

    # ==================================================
    # DETAILED TRANSCRIPTION
    # ==================================================

    def transcribe_detailed(self, audio):

        try:

            segments, info = (
                self.model.transcribe(
                    audio,
                    language=None,
                    beam_size=1,
                    best_of=1,
                    temperature=0,
                    vad_filter=True,
                    vad_parameters={
                        "min_silence_duration_ms": 450
                    },
                    condition_on_previous_text=False,
                )
            )

            parts = []

            log_probs = []

            no_speech = []

            count = 0

            for segment in segments:

                text = str(
                    getattr(
                        segment,
                        "text",
                        "",
                    )
                    or ""
                ).strip()

                if text:

                    parts.append(text)

                count += 1

                log_prob = getattr(
                    segment,
                    "avg_logprob",
                    None,
                )

                if log_prob is not None:

                    log_probs.append(
                        float(log_prob)
                    )

                no_prob = getattr(
                    segment,
                    "no_speech_prob",
                    None,
                )

                if no_prob is not None:

                    no_speech.append(
                        float(no_prob)
                    )

            text = (
                " ".join(parts).strip()
                or None
            )

            self.last_language = (
                getattr(
                    info,
                    "language",
                    None,
                )
                or "unknown"
            )

            self.last_language_probability = float(
                getattr(
                    info,
                    "language_probability",
                    0.0,
                )
                or 0.0
            )

            confidence = None

            if log_probs:

                confidence = max(
                    0.0,
                    min(
                        1.0,
                        1.0
                        + float(
                            np.mean(log_probs)
                        )
                        / 4.0,
                    ),
                )

            return {
                "text": text,
                "language": self.last_language,
                "language_probability": (
                    self.last_language_probability
                ),
                "confidence": confidence,
                "avg_logprob": (
                    float(np.mean(log_probs))
                    if log_probs
                    else None
                ),
                "no_speech_prob": (
                    float(np.max(no_speech))
                    if no_speech
                    else None
                ),
                "segments": count,
            }

        except Exception as error:

            print(
                f"❌ Detailed transcription "
                f"error: {error}"
            )

            return {
                "text": None,
                "language": "unknown",
                "language_probability": 0.0,
                "confidence": None,
                "avg_logprob": None,
                "no_speech_prob": None,
                "segments": 0,
            }

    # ==================================================
    # FILE TRANSCRIPTION (testing / debugging)
    # ==================================================

    def transcribe_file(self, path):

        try:

            with wave.open(
                str(path),
                "rb",
            ) as wav_file:

                rate = (
                    wav_file.getframerate()
                )

                channels = (
                    wav_file.getnchannels()
                )

                width = (
                    wav_file.getsampwidth()
                )

                frames = wav_file.readframes(
                    wav_file.getnframes()
                )

            if width == 2:

                audio = (
                    np.frombuffer(
                        frames,
                        dtype=np.int16,
                    )
                    .astype(np.float32)
                    / 32768.0
                )

            elif width == 4:

                audio = (
                    np.frombuffer(
                        frames,
                        dtype=np.int32,
                    )
                    .astype(np.float32)
                    / 2147483648.0
                )

            elif width == 1:

                audio = (
                    np.frombuffer(
                        frames,
                        dtype=np.uint8,
                    )
                    .astype(np.float32)
                    - 128.0
                ) / 128.0

            else:

                print(
                    "❌ Unsupported WAV sample width."
                )

                return None

            if channels > 1:

                audio = audio.reshape(
                    -1,
                    channels,
                ).mean(axis=1)

            if rate != self.sample_rate:

                count = int(
                    len(audio)
                    * self.sample_rate
                    / rate
                )

                if count > 0:

                    audio = np.interp(
                        np.linspace(
                            0,
                            len(audio) - 1,
                            count,
                        ),
                        np.arange(len(audio)),
                        audio,
                    )

            return self._transcribe(
                audio.astype(np.float32)
            )

        except Exception as error:

            print(
                f"❌ File transcription error: {error}"
            )

            return None

    # ==================================================
    # STATS
    # ==================================================

    def get_stats(self):

        stats = dict(self._stats)

        stats["energy_threshold"] = round(
            self.energy_threshold,
            4,
        )

        stats["noise_floor"] = (
            round(self.noise_floor, 4)
            if self.noise_floor is not None
            else None
        )

        stats["device"] = self.device

        stats["paused"] = self._paused

        stats["hallucination_filter"] = (
            self.hallucination_filter
        )

        return stats


# ------------------------------------------------------------
# DROP-IN UPGRADE
# voice_worker.py imports SpeechToText from this file and
# now gets the extended version automatically (same API).
# Delete the next line to keep using the original.
# ------------------------------------------------------------

SpeechToText = SpeechToTextPro

# ============================================================
# 🌙 ACCURACY BOOST — AUTO-APPLIED (APPEND ONLY)
# Requires voice/stt_accuracy.py in your project.
# ============================================================

try:

    from voice.stt_accuracy import (
        apply_accuracy_boost,
    )

    _LUNA_ACCURACY_OK = True

except ImportError:

    _LUNA_ACCURACY_OK = False


if _LUNA_ACCURACY_OK:

    class SpeechToTextUltra(type(SpeechToText)):

        def __init__(self):

            super().__init__()

            # Reads config.LUNA_STT_MODEL when set.

            apply_accuracy_boost(self)


    SpeechToText = SpeechToTextUltra

# ============================================================
# QUICK TEST (uncomment to try)
# ============================================================
#
# if __name__ == "__main__":
#
#     stt = SpeechToText()
#
#     print("Microphones:")
#     for mic in stt.list_microphones():
#         print(" ", mic)
#
#     stt.calibrate()
#     print(stt.get_stats())
#
#     print("Heard:", stt.listen())