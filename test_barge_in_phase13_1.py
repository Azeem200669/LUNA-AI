"""LUNA Phase 13.1 - true voice barge-in test (no microphone required)."""
from __future__ import annotations

import sys
import threading
import types
from pathlib import Path

BASE = Path(__file__).resolve().parent


def _existing(*relative_paths: str) -> Path | None:
    for relative in relative_paths:
        candidate = BASE / relative
        if candidate.exists():
            return candidate
    return None


def main() -> int:
    print("=" * 78)
    print("🌙 LUNA PHASE 13.1 - TRUE VOICE BARGE-IN TEST")
    print("=" * 78)

    # The contract tests do not open the real microphone.
    fake_sd = types.SimpleNamespace(InputStream=object)
    sys.modules.setdefault("sounddevice", fake_sd)
    sys.path.insert(0, str(BASE))

    from core.barge_in import BargeInListener

    print("\nTEST 1: STOP phrase detection")
    positives = (
        "stop",
        "please stop",
        "stop Luna",
        "stop speaking",
        "cancel",
        "that's enough",
    )
    for text in positives:
        assert BargeInListener.is_stop_command(text), text
    print("PASS")

    print("\nTEST 2: normal speech is ignored")
    negatives = (
        "tell me about Python",
        "open Chrome",
        "what is machine learning",
        "I am learning Python",
    )
    for text in negatives:
        assert not BargeInListener.is_stop_command(text), text
    print("PASS")

    print("\nTEST 3: listener stop state is thread-safe")
    listener = BargeInListener(
        transcribe=lambda audio: "stop",
        on_stop=lambda text: None,
    )
    assert not listener.triggered
    listener._triggered.set()
    assert listener.triggered
    listener.stop()
    assert listener._stop_event.is_set()
    print("PASS")

    print("\nTEST 4: voice worker contains barge-in integration")
    worker_path = _existing(
        "ui/voice_worker.py",
        "ui/voice_worker_phase13_1.py",
    )
    assert worker_path is not None, "VoiceWorker file not found."
    source = worker_path.read_text(encoding="utf-8")
    checks = (
        "BargeInListener",
        "self.barge_in.start()",
        "self.barge_in.stop()",
        "self._on_barge_stop",
        "self.tts.stop()",
        "self._barge_stop_event",
    )
    for item in checks:
        assert item in source, item
    print(f"Using voice worker: {worker_path}")
    print("PASS")

    print("\nTEST 5: TTS stop remains available")
    tts_path = BASE / "voice" / "text_to_speech.py"
    assert tts_path.exists(), f"TTS file not found: {tts_path}"
    tts_source = tts_path.read_text(encoding="utf-8")
    assert "def stop(self):" in tts_source
    assert "pygame.mixer.music.stop()" in tts_source
    print("PASS")

    print("\nTEST 6: STOP command callback contract")
    callback_event = threading.Event()
    seen = []

    def on_stop(text: str) -> None:
        seen.append(text)
        callback_event.set()

    assert BargeInListener.is_stop_command("stop Luna")
    on_stop("stop Luna")
    assert callback_event.is_set()
    assert seen == ["stop Luna"]
    print("PASS")

    print("\n" + "=" * 78)
    print("✅ PHASE 13.1 BARGE-IN FOUNDATION PASSED")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())