from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path.cwd()
if not (ROOT / "core" / "barge_in.py").exists():
    # Allow running this file from another directory.
    candidate = Path(__file__).resolve().parent
    if (candidate / "core" / "barge_in.py").exists():
        ROOT = candidate

BAR = ROOT / "core" / "barge_in.py"
STT = ROOT / "voice" / "speech_to_text.py"
TEST = ROOT / "test_voice_barge_in_phase14_5.py"

if not BAR.exists():
    raise SystemExit(f"ERROR: {BAR} not found. Run this script from the LUNA project root.")
if not STT.exists():
    raise SystemExit(f"ERROR: {STT} not found.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = ROOT / "backup_phase14_5" / stamp
backup.mkdir(parents=True, exist_ok=True)

for path in (BAR, STT, TEST):
    if path.exists():
        shutil.copy2(path, backup / path.name)

BAR_CODE = r'''"""LUNA Phase 14.5 - robust low-latency voice barge-in listener.

The listener is intentionally independent from the main VoiceWorker STT loop.
It uses the existing SpeechToText Whisper model callback, but automatically
selects the dedicated English command transcription method when available.

Fixes in this version:
- avoids loopback / Stereo Mix / virtual cable input when possible
- adaptive noise floor instead of an overly low fixed VAD threshold
- pre-roll + consecutive-block speech start confirmation
- no silent-audio fallback transcription
- shorter, cleaner command segments
- dedicated English command transcription path
- generation-safe callback remains in VoiceWorker
"""
from __future__ import annotations

import os
import queue
import re
import threading
import time
from collections import deque
from typing import Callable, Optional

import numpy as np
import sounddevice as sd


class BargeInListener:
    """Listen for an explicit spoken STOP command while LUNA is speaking."""

    STOP_PHRASES = {
        "stop",
        "stop luna",
        "stop speaking",
        "stop it",
        "cancel",
        "cancel luna",
        "be quiet",
        "quiet",
        "that's enough",
        "thats enough",
        "enough",
        "stopped",
        "stopping",
        "stoped",
        "stoping",
    }

    STOP_KEYWORDS = ("stop", "cancel")

    LOOPBACK_HINTS = (
        "stereo mix",
        "what u hear",
        "what you hear",
        "loopback",
        "cable output",
        "cable input",
        "vb-audio",
        "voicemeeter output",
        "voicemeeter out",
        "virtual audio",
        "wave out mix",
    )

    MIC_HINTS = (
        "microphone",
        "mic",
        "headset",
        "headphone mic",
        "communications",
        "array",
    )

    def __init__(
        self,
        transcribe: Callable[[np.ndarray], Optional[str]],
        on_stop: Callable[[str], None],
        sample_rate: int = 16000,
        block_duration: float = 0.10,
        energy_threshold: float = 0.012,
        noise_multiplier: float = 3.2,
        silence_duration: float = 0.40,
        max_capture_time: float = 1.80,
        min_capture_time: float = 0.25,
        calibration_time: float = 0.60,
        input_device: int | str | None = None,
    ) -> None:
        self.transcribe = transcribe
        self.on_stop = on_stop
        self.sample_rate = int(sample_rate)
        self.block_duration = float(block_duration)
        self.block_size = max(1, int(self.sample_rate * self.block_duration))
        self.base_energy_threshold = float(energy_threshold)
        self.energy_threshold = float(energy_threshold)
        self.noise_multiplier = float(noise_multiplier)
        self.silence_duration = float(silence_duration)
        self.max_capture_time = float(max_capture_time)
        self.min_capture_time = float(min_capture_time)
        self.calibration_time = float(calibration_time)

        self.input_device = self._resolve_input_device(input_device)
        self.input_device_name = self._device_name(self.input_device)

        self._stop_event = threading.Event()
        self._triggered = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running_lock = threading.Lock()

        print(
            f"[LUNA BARGE-IN] input device: "
            f"{self.input_device} - {self.input_device_name}"
        )

        # Automatically use the specialized command decoder when the bound
        # SpeechToText object exposes one. This keeps VoiceWorker unchanged.
        bound_owner = getattr(transcribe, "__self__", None)
        specialized = getattr(bound_owner, "_transcribe_barge_in", None)
        if callable(specialized):
            self._command_transcribe = specialized
        else:
            self._command_transcribe = transcribe

    @property
    def triggered(self) -> bool:
        return self._triggered.is_set()

    @property
    def running(self) -> bool:
        thread = self._thread
        return bool(thread and thread.is_alive())

    @staticmethod
    def normalize_command(text: str) -> str:
        text = re.sub(r"\s+", " ", str(text or "").strip().lower())
        text = re.sub(r"[^\w\s']+", "", text, flags=re.UNICODE)
        return text.strip()

    @classmethod
    def is_stop_command(cls, text: str) -> bool:
        normalized = cls.normalize_command(text)
        if not normalized:
            return False

        if normalized in cls.STOP_PHRASES:
            return True

        words = normalized.split()
        word_set = set(words)

        # Natural requests such as "please stop" or "stop Luna now".
        if word_set.intersection(cls.STOP_KEYWORDS):
            return True

        # Whisper commonly produces minor suffix/past-tense variations.
        if len(words) <= 2 and any(
            word in {"stop", "stopped", "stopping", "stoped", "stoping"}
            for word in words
        ):
            return True

        return False

    @classmethod
    def _device_name(cls, device) -> str:
        try:
            info = sd.query_devices(device)
            return str(info.get("name", "unknown"))
        except Exception:
            return "unknown"

    @classmethod
    def _resolve_input_device(cls, requested):
        # Explicit environment override wins.
        env_device = os.getenv("LUNA_BARGEIN_INPUT_DEVICE", "").strip()
        if requested is None and env_device:
            requested = env_device

        if requested not in (None, ""):
            try:
                requested_index = int(requested)
                info = sd.query_devices(requested_index)
                if int(info.get("max_input_channels", 0)) > 0:
                    return requested_index
            except Exception:
                pass

        try:
            default_input = sd.default.device[0]
        except Exception:
            default_input = None

        devices = []
        try:
            devices = list(sd.query_devices())
        except Exception:
            devices = []

        def is_valid_input(info):
            try:
                return int(info.get("max_input_channels", 0)) > 0
            except Exception:
                return False

        def name(info):
            return str(info.get("name", "")).lower()

        # If the default is a loopback/virtual input, prefer a physical mic.
        if default_input is not None:
            try:
                default_info = sd.query_devices(default_input)
                default_name = name(default_info)
                if is_valid_input(default_info) and not any(
                    hint in default_name for hint in cls.LOOPBACK_HINTS
                ):
                    return int(default_input)
            except Exception:
                pass

        preferred = []
        fallback = []
        for index, info in enumerate(devices):
            if not is_valid_input(info):
                continue
            lowered = name(info)
            if any(hint in lowered for hint in cls.LOOPBACK_HINTS):
                continue
            if any(hint in lowered for hint in cls.MIC_HINTS):
                preferred.append(index)
            else:
                fallback.append(index)

        if preferred:
            return preferred[0]
        if fallback:
            return fallback[0]

        # Last resort: PortAudio default.
        if default_input is not None:
            return int(default_input)
        return None

    def _calibrate_noise(self, stream_queue: queue.Queue[np.ndarray]) -> None:
        samples = []
        deadline = time.monotonic() + self.calibration_time

        while not self._stop_event.is_set() and time.monotonic() < deadline:
            remaining = max(0.01, min(0.10, deadline - time.monotonic()))
            try:
                audio = stream_queue.get(timeout=remaining)
            except queue.Empty:
                continue

            if audio.size == 0:
                continue

            rms = float(np.sqrt(np.mean(audio * audio)))
            samples.append(rms)

        if not samples:
            self.energy_threshold = self.base_energy_threshold
            return

        # Lower percentile reduces the chance that speech or loud music during
        # startup becomes the estimated noise floor.
        noise_floor = float(np.percentile(np.asarray(samples), 25))
        self.energy_threshold = max(
            self.base_energy_threshold,
            noise_floor * self.noise_multiplier,
        )

        print(
            f"[LUNA BARGE-IN] noise floor={noise_floor:.4f} "
            f"threshold={self.energy_threshold:.4f}"
        )

    def start(self) -> None:
        with self._running_lock:
            if self._thread is not None and self._thread.is_alive():
                return

            self._stop_event.clear()
            self._triggered.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="LUNA-Barge-In",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if (
            thread is not None
            and thread.is_alive()
            and thread is not threading.current_thread()
        ):
            thread.join(timeout=1.0)

    def _run(self) -> None:
        audio_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=40)

        def callback(indata, frames, time_info, status) -> None:
            if self._stop_event.is_set():
                return
            try:
                audio = np.asarray(indata[:, 0], dtype=np.float32).copy()
                try:
                    audio_queue.put_nowait(audio)
                except queue.Full:
                    try:
                        audio_queue.get_nowait()
                    except queue.Empty:
                        pass
                    try:
                        audio_queue.put_nowait(audio)
                    except queue.Full:
                        pass
            except Exception:
                pass

        stream_kwargs = {
            "samplerate": self.sample_rate,
            "channels": 1,
            "dtype": "float32",
            "blocksize": self.block_size,
            "callback": callback,
        }
        if self.input_device is not None:
            stream_kwargs["device"] = self.input_device

        try:
            with sd.InputStream(**stream_kwargs):
                print("[LUNA BARGE-IN] microphone stream opened")

                self._calibrate_noise(audio_queue)

                while not self._stop_event.is_set():
                    speech = self._capture_segment(audio_queue)
                    if speech is None:
                        continue

                    if self._stop_event.is_set():
                        return

                    duration = len(speech) / float(self.sample_rate)
                    rms = float(np.sqrt(np.mean(speech * speech))) if speech.size else 0.0

                    # Never feed tiny/no-speech segments into Whisper.
                    if duration < self.min_capture_time or rms < self.energy_threshold * 0.90:
                        continue

                    print(
                        f"[LUNA BARGE-IN] captured segment: "
                        f"duration={duration:.2f}s rms={rms:.4f} transcribing..."
                    )

                    try:
                        text = self._command_transcribe(speech)
                    except Exception as error:
                        print(f"[LUNA BARGE-IN] transcription warning: {error}")
                        continue

                    if self._stop_event.is_set():
                        return

                    print(f"[LUNA BARGE-IN] transcribed: {text!r}")

                    if self.is_stop_command(text):
                        self._triggered.set()
                        print(f"[LUNA BARGE-IN] STOP detected: {text}")
                        try:
                            self.on_stop(str(text))
                        except Exception as error:
                            print(
                                f"[LUNA BARGE-IN] stop callback warning: {error}"
                            )
                        return

        except Exception as error:
            print(f"[LUNA BARGE-IN] microphone warning: {error}")

    def _capture_segment(
        self,
        audio_queue: queue.Queue[np.ndarray],
    ) -> Optional[np.ndarray]:
        chunks: list[np.ndarray] = []
        pre_roll = deque(maxlen=5)
        speech_started = False
        consecutive_voice = 0
        start_time = 0.0
        last_voice_time = 0.0
        deadline = time.monotonic() + self.max_capture_time

        while not self._stop_event.is_set():
            if time.monotonic() >= deadline:
                break

            try:
                audio = audio_queue.get(timeout=0.10)
            except queue.Empty:
                continue

            if audio.size == 0:
                continue

            pre_roll.append(audio)
            now = time.monotonic()
            rms = float(np.sqrt(np.mean(audio * audio)))

            if rms >= self.energy_threshold:
                consecutive_voice += 1
            else:
                consecutive_voice = 0

            if not speech_started:
                # Require two consecutive voiced blocks to suppress transient
                # keyboard clicks / background pops / single noisy frames.
                if consecutive_voice >= 2:
                    speech_started = True
                    start_time = now
                    last_voice_time = now
                    chunks.extend(list(pre_roll))
                    print(
                        f"[LUNA BARGE-IN] VAD: speech started "
                        f"rms={rms:.4f} threshold={self.energy_threshold:.4f}"
                    )
                continue

            chunks.append(audio)

            if rms >= self.energy_threshold:
                last_voice_time = now

            speech_time = now - start_time
            silence_time = now - last_voice_time

            if (
                speech_time >= self.min_capture_time
                and silence_time >= self.silence_duration
            ):
                print(
                    f"[LUNA BARGE-IN] VAD: end-of-speech "
                    f"speech={speech_time:.2f}s silence={silence_time:.2f}s"
                )
                break

        if not speech_started or not chunks:
            return None

        return np.concatenate(chunks).astype(np.float32)
'''

BAR.write_text(BAR_CODE, encoding="utf-8")

stt_text = STT.read_text(encoding="utf-8")

method = r'''    # ========================================================
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

'''

marker = "    # ========================================================\n    # LISTEN\n    # ========================================================"
if marker not in stt_text:
    raise SystemExit("ERROR: Could not find SpeechToText LISTEN marker. No STT file changes were made.")

# Remove any previous copy of the method, then insert once immediately before LISTEN.
stt_text = re.sub(
    r"\n    # ========================================================\n    # BARGE-IN COMMAND TRANSCRIPTION\n    # ========================================================\n.*?(?=    # ========================================================\n    # LISTEN\n    # ========================================================)",
    "\n",
    stt_text,
    flags=re.S,
)
stt_text = stt_text.replace(marker, method + marker, 1)
STT.write_text(stt_text, encoding="utf-8")

TEST_CODE = r'''"""LUNA Phase 14.5 V3 - voice + true barge-in stress test."""
from __future__ import annotations

import inspect
import sys
import threading
import time
import traceback
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from voice.speech_to_text import SpeechToText
from voice.text_to_speech import TextToSpeech
from core.barge_in import BargeInListener
from core.stop_control import GenerationGuard
from ui.voice_worker import VoiceWorker


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    print("=" * 78)
    print("🌙 LUNA PHASE 14.5 V3 - TRUE VOICE BARGE-IN TEST")
    print("=" * 78)
    print(f"PROJECT ROOT: {BASE}")

    started_all = time.perf_counter()
    stt = None
    tts = None
    listener = None
    worker = None

    try:
        print("\nTEST 1: Voice infrastructure")
        require(SpeechToText and TextToSpeech and VoiceWorker and BargeInListener,
                "Required voice classes failed to import")
        print("PASS")

        print("\nTEST 2: STT initialization")
        t = time.perf_counter()
        stt = SpeechToText()
        print(f"TIME: {time.perf_counter() - t:.3f}s")
        print(f"SAMPLE RATE: {stt.sample_rate}")
        require(stt.sample_rate == 16000, "Unexpected sample rate")
        require(callable(getattr(stt, "_transcribe_barge_in", None)),
                "Dedicated barge-in transcription method missing")
        print("PASS")

        print("\nTEST 3: TTS initialization")
        t = time.perf_counter()
        tts = TextToSpeech()
        print(f"TIME: {time.perf_counter() - t:.3f}s")
        require(getattr(tts, "audio_ready", False), "TTS audio system not ready")
        require(callable(getattr(tts, "stop", None)), "TTS stop() missing")
        print("PASS")

        print("\nTEST 4: Multilingual TTS detection")
        checks = {
            "Hello Luna": "en",
            "नमस्ते लूना": "hi",
            "హలో లూనా": "te",
            "வணக்கம் லூனா": "ta",
            "ಹಲೋ ಲೂನಾ": "kn",
            "こんにちはルナ": "ja",
        }
        for text, expected in checks.items():
            actual = tts.detect_text_language(text)
            print(f"{expected}: {actual}")
            require(actual == expected, f"Language detection failed for {text}")
        print("PASS")

        print("\nTEST 5: STOP command recognition contract")
        positives = ("stop", "please stop", "stop Luna", "stop speaking", "cancel", "cancel Luna", "be quiet", "that's enough")
        negatives = ("tell me about Python", "open Chrome", "search YouTube", "what is machine learning")
        for x in positives:
            require(BargeInListener.is_stop_command(x), x)
        for x in negatives:
            require(not BargeInListener.is_stop_command(x), x)
        print(f"POSITIVE: {len(positives)}")
        print(f"NEGATIVE: {len(negatives)}")
        print("PASS")

        print("\nTEST 6: GenerationGuard")
        guard = GenerationGuard()
        a = guard.next()
        b = guard.next()
        require(b > a, "Generation counter not monotonic")
        require(guard.is_current(b), "Latest generation is not current")
        require(not guard.is_current(a), "Old generation still current")
        print("PASS")

        print("\nTEST 7: VoiceWorker barge-in wiring")
        src = (BASE / "ui" / "voice_worker.py").read_text(encoding="utf-8")
        for term in (
            "BargeInListener",
            "_speech_guard",
            "_active_speech_generation",
            "_barge_stop_event",
            "_on_barge_stop",
            "self.barge_in.start()",
            "self.barge_in.stop()",
            "self.tts.stop()",
        ):
            require(term in src, f"Missing VoiceWorker wiring: {term}")
        print("PASS")

        print("\nTEST 8: Real microphone BargeInListener")
        print("IMPORTANT: pause YouTube/music/video playback before this test.")
        print("The test auto-avoids common loopback/virtual audio inputs.")
        input("Press ENTER, then say: STOP LUNA\n")

        stop_event = threading.Event()
        callback_data = {"text": None}

        def on_stop(text):
            callback_data["text"] = text
            print(f"🛑 CALLBACK: {text}")
            stop_event.set()

        listener = BargeInListener(
            transcribe=stt._transcribe,
            on_stop=on_stop,
        )

        print()
        print(f"INPUT DEVICE: {listener.input_device} - {listener.input_device_name}")
        listener.start()
        print("🎙️ LISTENER ACTIVE — say STOP LUNA now")

        t = time.perf_counter()
        detected = stop_event.wait(timeout=20.0)
        duration = time.perf_counter() - t
        listener.stop()

        require(detected, "Barge-in STOP was not detected within 20 seconds")
        require(listener.triggered, "Listener did not enter triggered state")
        require(callback_data["text"], "STOP callback text missing")
        require(BargeInListener.is_stop_command(callback_data["text"]),
                f"Callback text not recognized as STOP: {callback_data['text']}")
        print(f"DETECTED: {callback_data['text']}")
        print(f"TIME: {duration:.3f}s")
        print("PASS")

        print("\nTEST 9: True TTS + barge-in interruption")
        print("LUNA will speak a long response.")
        print("Say STOP LUNA while it is speaking.")

        tts_stopped = threading.Event()
        speech_finished = threading.Event()
        callback_text = {"value": None}

        def integrated_stop(text):
            callback_text["value"] = text
            print(f"🛑 TRUE BARGE-IN: {text}")
            tts.stop()
            tts_stopped.set()

        integrated_listener = BargeInListener(
            transcribe=stt._transcribe,
            on_stop=integrated_stop,
        )

        long_text = (
            "LUNA is currently delivering a long response for the interruption test. "
            "Please speak the command stop Luna at any point while this sentence is being spoken. "
            "The audio should stop immediately when the spoken interruption is detected."
        )

        def speak():
            try:
                tts.speak(long_text, language="en")
            finally:
                speech_finished.set()

        speech_thread = threading.Thread(target=speak, daemon=True)
        integrated_listener.start()
        started = time.perf_counter()
        speech_thread.start()

        print("🔊 LUNA SPEAKING — say STOP LUNA now")
        interrupted = tts_stopped.wait(timeout=20.0)

        # Give pygame/edge-tts a moment to unwind after stop().
        speech_thread.join(timeout=5.0)
        integrated_listener.stop()

        duration = time.perf_counter() - started

        require(interrupted, "TTS was not interrupted by the spoken STOP command")
        require(not speech_thread.is_alive(), "TTS speech thread did not finish after interruption")
        require(not getattr(tts, "speaking", False), "TTS still reports speaking")
        require(callback_text["value"], "Integrated STOP callback did not fire")
        print(f"INTERRUPTED BY: {callback_text['value']}")
        print(f"TIME: {duration:.3f}s")
        print("PASS")

        print("\nTEST 10: VoiceWorker clean shutdown")
        worker = VoiceWorker()
        # Isolate Qt shutdown from the real blocking Whisper loop.
        worker.stt.listen = lambda: None
        worker.start()
        time.sleep(0.15)
        t = time.perf_counter()
        worker.stop()
        worker.wait(3000)
        duration = time.perf_counter() - t
        require(not worker.isRunning(), "VoiceWorker failed to stop cleanly")
        print(f"TIME: {duration:.3f}s")
        print("WORKER RUNNING: False")
        print("PASS")

        total = time.perf_counter() - started_all
        print()
        print("=" * 78)
        print("✅ PHASE 14.5 V3 PASSED — TRUE VOICE BARGE-IN VERIFIED")
        print(f"TOTAL TIME: {total:.3f}s")
        print("=" * 78)
        return 0

    except Exception as error:
        print()
        print("=" * 78)
        print("❌ PHASE 14.5 V3 FAILED")
        print("=" * 78)
        print(f"ERROR: {error}")
        traceback.print_exc()
        return 1

    finally:
        try:
            if listener is not None:
                listener.stop()
        except Exception:
            pass
        try:
            if worker is not None and worker.isRunning():
                worker.stop()
                worker.wait(3000)
        except Exception:
            pass
        try:
            if tts is not None:
                tts.stop()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
'''

TEST.write_text(TEST_CODE, encoding="utf-8")

print(f"✅ Phase 14.5 barge-in fix installed in: {ROOT}")
print(f"✅ Backup created at: {backup}")
print("✅ Rewritten: core/barge_in.py")
print("✅ Patched: voice/speech_to_text.py")
print("✅ Rewritten: test_voice_barge_in_phase14_5.py")
print()
print("Next command:")
print("python test_voice_barge_in_phase14_5.py")