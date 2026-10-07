"""LUNA Phase 13.2 - STOP race-condition and stale callback test (fixed paths)."""
from __future__ import annotations

import threading
from pathlib import Path

BASE = Path(__file__).resolve().parent


def first_existing(*paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path
    raise FileNotFoundError(
        "None of the expected files exist:\n" +
        "\n".join(f"- {path}" for path in paths)
    )


def main() -> int:
    print("=" * 78)
    print("🌙 LUNA PHASE 13.2 - STOP RACE-CONDITION TEST")
    print("=" * 78)

    # Test the actual installed project files first. The backup filenames are
    # accepted as a convenience when the phase files have not yet been
    # renamed/copied into ui/.
    window_path = first_existing(
        BASE / "ui" / "window.py",
        BASE / "window_phase13_2.py",
    )
    voice_path = first_existing(
        BASE / "ui" / "voice_worker.py",
        BASE / "voice_worker_phase13_2.py",
    )

    print(f"Using window: {window_path}")
    print(f"Using voice worker: {voice_path}")

    from core.stop_control import GenerationGuard

    print("\nTEST 1: generation invalidation")
    guard = GenerationGuard()
    first = guard.next()
    second = guard.next()
    assert second != first
    assert not guard.is_current(first)
    assert guard.is_current(second)
    print("PASS")

    print("\nTEST 2: concurrent generation access")
    tokens = []
    lock = threading.Lock()

    def producer():
        token = guard.next()
        with lock:
            tokens.append(token)

    threads = [threading.Thread(target=producer) for _ in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(tokens) == 20
    assert len(set(tokens)) == 20
    assert guard.current() in tokens
    print("PASS")

    window = window_path.read_text(encoding="utf-8")
    voice = voice_path.read_text(encoding="utf-8")

    print("\nTEST 3: stale AI response suppression contract")
    checks = (
        "GenerationGuard",
        "self._generation_guard.is_current(worker.generation)",
        "generation=generation",
        "self._generation_guard.invalidate()",
        "lambda gen=tts_generation: self.tts_finished(gen)",
    )
    for item in checks:
        assert item in window, f"Missing window contract: {item}"
    print("PASS")

    print("\nTEST 4: stale TTS completion suppression contract")
    checks = (
        "self._active_tts_generation",
        "generation != self._active_tts_generation",
        "self._generation_guard.is_current(generation",
    )
    for item in checks:
        assert item in window, f"Missing TTS contract: {item}"
    print("PASS")

    print("\nTEST 5: stale voice barge-in suppression contract")
    checks = (
        "self._speech_guard",
        "self._active_speech_generation",
        "on_stop=lambda detected, gen=speech_generation",
        "generation != self._active_speech_generation",
        "Ignoring stale barge-in STOP callback",
    )
    for item in checks:
        assert item in voice, f"Missing voice contract: {item}"
    print("PASS")

    print("\nTEST 6: STOP invalidates speech generation")
    stop_index = voice.index("    def stop(self):")
    stop_block = voice[stop_index:]
    assert "self._speech_guard.invalidate()" in stop_block
    assert "self._active_speech_generation = 0" in stop_block
    assert "self.tts.stop()" in stop_block
    print("PASS")

    print("\n" + "=" * 78)
    print("✅ PHASE 13.2 STOP RACE PROTECTION PASSED")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())