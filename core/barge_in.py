"""LUNA Phase 14.5 - robust low-latency voice barge-in listener.

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
