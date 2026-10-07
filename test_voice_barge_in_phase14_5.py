"""LUNA Phase 14.5 V3 - voice + true barge-in stress test."""
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
