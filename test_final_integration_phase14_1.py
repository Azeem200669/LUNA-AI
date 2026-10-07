"""LUNA Phase 14.1 - final integration and architecture smoke test.

This test intentionally avoids launching the GUI, microphone, browser, or live AI
provider. It verifies that the Phase 12-13 building blocks coexist, compile, and
expose the contracts required by the final LUNA application.
"""
from __future__ import annotations

import ast
import concurrent.futures
import py_compile
import sys
import tempfile
import threading
from pathlib import Path

BASE = Path(__file__).resolve().parent

REQUIRED_FILES = (
    "main_ui.py",
    "core/agent.py",
    "core/memory.py",
    "core/memory_extractor.py",
    "core/memory_retriever.py",
    "core/memory_controls.py",
    "core/stop_control.py",
    "core/barge_in.py",
    "ui/window.py",
    "ui/voice_worker.py",
    "voice/text_to_speech.py",
    "voice/speech_to_text.py",
    "browser/browser_controller.py",
    "core/action_executor.py",
    "nlp/nlp_engine.py",
    "nlp/planner.py",
    "core/fast_router.py",
)


def assert_contains(path: Path, *terms: str) -> None:
    text = path.read_text(encoding="utf-8")
    for term in terms:
        assert term in text, f"{term!r} missing from {path}"


def main() -> int:
    print("=" * 78)
    print("🌙 LUNA PHASE 14.1 - FINAL INTEGRATION TEST")
    print("=" * 78)
    print(f"PROJECT: {BASE}")

    # ------------------------------------------------------------------
    # TEST 1: required project surface
    # ------------------------------------------------------------------
    print("\nTEST 1: required LUNA files")
    missing = [p for p in REQUIRED_FILES if not (BASE / p).is_file()]
    assert not missing, "Missing files:\n" + "\n".join(f"- {p}" for p in missing)
    print(f"FOUND: {len(REQUIRED_FILES)} required files")
    print("PASS")

    # ------------------------------------------------------------------
    # TEST 2: compile the core application Python surface
    # ------------------------------------------------------------------
    print("\nTEST 2: Python compilation")
    compile_targets = [
        BASE / p for p in REQUIRED_FILES
    ]
    for path in compile_targets:
        py_compile.compile(str(path), doraise=True)
    print(f"COMPILED: {len(compile_targets)} files")
    print("PASS")

    # ------------------------------------------------------------------
    # TEST 3: syntax/structure sanity via AST
    # ------------------------------------------------------------------
    print("\nTEST 3: critical class/function structure")
    checks = {
        "core/agent.py": ("LunaAgent",),
        "core/memory.py": ("MemoryManager",),
        "core/memory_extractor.py": ("MemoryExtractor",),
        "core/memory_retriever.py": ("MemoryRetriever",),
        "core/memory_controls.py": ("MemoryControls",),
        "core/stop_control.py": ("GenerationGuard",),
        "core/barge_in.py": ("BargeInListener",),
        "ui/window.py": ("LunaWindow", "AIWorker", "TTSWorker"),
        "ui/voice_worker.py": ("VoiceWorker",),
        "voice/text_to_speech.py": ("TextToSpeech",),
        "browser/browser_controller.py": ("BrowserController",),
        "nlp/nlp_engine.py": ("NLPEngine",),
        "nlp/planner.py": ("LunaPlanner",),
        "core/fast_router.py": ("FastRouter",),
    }
    for relative, names in checks.items():
        tree = ast.parse((BASE / relative).read_text(encoding="utf-8"), filename=relative)
        defined = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for name in names:
            assert name in defined, f"{name} missing from {relative}"
    print("PASS")

    # ------------------------------------------------------------------
    # TEST 4: memory pipeline works together
    # ------------------------------------------------------------------
    print("\nTEST 4: memory pipeline integration")
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "memory.db"
        from core.memory import MemoryManager
        from core.memory_extractor import MemoryExtractor
        from core.memory_retriever import MemoryRetriever
        from core.memory_controls import MemoryControls

        memory = MemoryManager(db_path)
        try:
            extractor = MemoryExtractor()
            retriever = MemoryRetriever(memory)
            controls = MemoryControls(memory)

            extracted = extractor.save(memory, "I am working on an anime card game.")
            assert extracted is not None
            assert extracted["memory_type"] == "project"
            assert memory.get_memory("project_current") is not None

            found = retriever.retrieve("What game am I working on?")
            assert found
            assert found[0]["memory_key"] == "project_current"

            response = controls.handle("forget my anime card game")
            assert response is not None
            assert memory.get_memory("project_current") is None
        finally:
            memory.close()
    print("PASS")

    # ------------------------------------------------------------------
    # TEST 5: generation guard concurrency
    # ------------------------------------------------------------------
    print("\nTEST 5: STOP generation concurrency")
    from core.stop_control import GenerationGuard

    guard = GenerationGuard()
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        tokens = list(pool.map(lambda _: guard.next(), range(50)))
    assert len(tokens) == 50
    assert len(set(tokens)) == 50
    assert guard.current() == max(tokens)
    assert guard.is_current(max(tokens))
    assert not guard.is_current(min(tokens))
    print("PASS")

    # ------------------------------------------------------------------
    # TEST 6: barge-in + TTS STOP contracts
    # ------------------------------------------------------------------
    print("\nTEST 6: voice interruption contracts")
    from core.barge_in import BargeInListener

    assert BargeInListener.is_stop_command("please stop")
    assert BargeInListener.is_stop_command("stop Luna")
    assert BargeInListener.is_stop_command("that's enough")
    assert not BargeInListener.is_stop_command("tell me about Python")

    tts_source = (BASE / "voice/text_to_speech.py").read_text(encoding="utf-8")
    assert "def stop(self)" in tts_source
    assert "pygame.mixer.music.stop()" in tts_source

    voice_source = (BASE / "ui/voice_worker.py").read_text(encoding="utf-8")
    assert "BargeInListener" in voice_source
    assert "self.barge_in.start()" in voice_source
    assert "self.barge_in.stop()" in voice_source
    assert "self._on_barge_stop" in voice_source
    print("PASS")

    # ------------------------------------------------------------------
    # TEST 7: agent memory + browser lifecycle surface
    # ------------------------------------------------------------------
    print("\nTEST 7: agent integration contracts")
    agent_source = (BASE / "core/agent.py").read_text(encoding="utf-8")
    assert "MemoryManager" in agent_source
    assert "MemoryRetriever" in agent_source
    assert "MemoryExtractor" in agent_source
    assert "MemoryControls" in agent_source
    assert "_BrowserWorker" in agent_source
    assert "def shutdown(self):" in agent_source
    assert "worker.shutdown()" in agent_source
    print("PASS")

    # ------------------------------------------------------------------
    # TEST 8: UI STOP race protection surface
    # ------------------------------------------------------------------
    print("\nTEST 8: UI final STOP protection")
    window_source = (BASE / "ui/window.py").read_text(encoding="utf-8")
    assert "GenerationGuard" in window_source
    assert "self._generation_guard.is_current(worker.generation)" in window_source
    assert "self._generation_guard.invalidate()" in window_source
    assert "def stop_all(self, reason=\"user\")" in window_source
    assert "event.key() == Qt.Key_Escape" in window_source

    # ------------------------------------------------------------------
    # TEST 9: application entry point surface
    # ------------------------------------------------------------------
    print("\nTEST 9: application entry point")
    main_ui_source = (BASE / "main_ui.py").read_text(encoding="utf-8")
    assert "QApplication" in main_ui_source
    assert "LunaWindow" in main_ui_source
    assert ".show()" in main_ui_source
    assert ".exec()" in main_ui_source or ".exec_()" in main_ui_source
    print("PASS")

    # ------------------------------------------------------------------
    # TEST 10: project package hygiene
    # ------------------------------------------------------------------
    print("\nTEST 10: package markers")
    package_dirs = ("core", "ui", "voice", "nlp", "browser", "tools", "web")
    for package in package_dirs:
        init_file = BASE / package / "__init__.py"
        assert init_file.exists(), f"Missing package marker: {init_file}"
    print("PASS")

    print("\n" + "=" * 78)
    print("✅ PHASE 14.1 FINAL INTEGRATION PASSED")
    print("=" * 78)
    print("NOTE: This is a no-hardware integration smoke test; microphone, GUI, browser, and live Groq calls are not launched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())