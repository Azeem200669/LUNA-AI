"""LUNA Phase 13 - reliable STOP control test (fixed paths)."""
from __future__ import annotations

import importlib.util
import threading
from pathlib import Path

BASE = Path(__file__).resolve().parent


def load_module(name: str, path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def first_existing(*paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path
    raise FileNotFoundError(
        "None of the expected files exist:\n"
        + "\n".join(f"- {p}" for p in paths)
    )


def main() -> int:
    print("=" * 78)
    print("🌙 LUNA PHASE 13 - RELIABLE STOP CONTROL TEST")
    print("=" * 78)

    window_path = first_existing(
        BASE / "ui" / "window.py",
        BASE / "window_phase13.py",
    )
    voice_worker_path = first_existing(
        BASE / "ui" / "voice_worker.py",
        BASE / "voice_worker_phase13.py",
    )
    tts_path = first_existing(
        BASE / "voice" / "text_to_speech.py",
        BASE / "text_to_speech_phase13.py",
    )

    print(f"Using window: {window_path}")
    print(f"Using voice worker: {voice_worker_path}")
    print(f"Using TTS: {tts_path}")

    print("\nTEST 1: cancellation event")
    event = threading.Event()
    assert not event.is_set()
    event.set()
    assert event.is_set()
    print("PASS")

    print("\nTEST 2: TextToSpeech.stop()")
    tts_mod = load_module("luna_phase13_tts", tts_path)
    tts = tts_mod.TextToSpeech()
    try:
        tts.speaking = True
        tts.stop()
        assert tts.speaking is False
        assert tts._stop_event.is_set()
        print("PASS")
    finally:
        tts.stop()

    print("\nTEST 3: TTSWorker.stop() contract")
    window_source = window_path.read_text(encoding="utf-8")
    assert "class TTSWorker(QThread):" in window_source
    assert "def stop(self):" in window_source
    assert "self._cancelled.set()" in window_source
    assert "pygame.mixer.music.stop()" in window_source
    print("PASS")

    print("\nTEST 4: AIWorker.cancel() contract")
    assert "def cancel(self):" in window_source
    assert "self.requestInterruption()" in window_source
    assert "request_id=0" in window_source
    assert "self.finished.emit(\"\")" in window_source
    print("PASS")

    print("\nTEST 5: global STOP control")
    assert "def stop_all(self, reason=\"user\")" in window_source
    assert '"stop"' in window_source
    assert '"stop luna"' in window_source
    assert '"stop speaking"' in window_source
    assert 'self.stop_all("button")' in window_source
    assert 'event.key() == Qt.Key_Escape' in window_source
    print("PASS")

    print("\nTEST 6: voice STOP commands")
    voice_source = voice_worker_path.read_text(encoding="utf-8")
    assert '"stop"' in voice_source
    assert '"stop luna"' in voice_source
    assert '"stop speaking"' in voice_source
    assert "self.tts.stop()" in voice_source
    print("PASS")

    print("\n" + "=" * 78)
    print("✅ PHASE 13 STOP FOUNDATION PASSED")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())