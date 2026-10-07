"""
LUNA Phase 14.7 - Packaging / Release Preflight

Run from the LUNA project root:

    python test_packaging_preflight_phase14_7.py

This does NOT build the final executable.
It verifies that the project is ready for a Windows packaging pass.
"""

from __future__ import annotations

import ast
import importlib
import os
import py_compile
import re
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent


REQUIRED_FILES = (
    "main_ui.py",
    "config.py",
    "core/agent.py",
    "core/memory.py",
    "core/memory_extractor.py",
    "core/memory_retriever.py",
    "core/memory_controls.py",
    "core/stop_control.py",
    "core/barge_in.py",
    "core/action_executor.py",
    "core/fast_router.py",
    "nlp/nlp_engine.py",
    "nlp/planner.py",
    "voice/speech_to_text.py",
    "voice/text_to_speech.py",
    "ui/window.py",
    "ui/voice_worker.py",
    "browser/browser_controller.py",
)


IMPORTS = (
    ("PySide6", "PySide6"),
    ("numpy", "numpy"),
    ("sounddevice", "sounddevice"),
    ("faster_whisper", "faster_whisper"),
    ("pygame", "pygame"),
    ("edge_tts", "edge_tts"),
    ("playwright", "playwright"),
)


SECRET_PATTERNS = (
    r'(?i)api[_-]?key\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']',
    r'(?i)groq[_-]?api[_-]?key\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']',
    r'(?i)gemini[_-]?api[_-]?key\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']',
    r'(?i)tavily[_-]?api[_-]?key\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']',
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run() -> int:
    print("=" * 78)
    print("🌙 LUNA PHASE 14.7 - PACKAGING / RELEASE PREFLIGHT")
    print("=" * 78)
    print(f"PROJECT ROOT: {BASE}")
    print(f"PYTHON: {sys.version.split()[0]}")
    print()

    passed = 0
    started = os.times()

    try:
        # ------------------------------------------------------------
        # TEST 1
        # ------------------------------------------------------------
        print("TEST 1: Required release files")

        missing = [
            item for item in REQUIRED_FILES
            if not (BASE / item).is_file()
        ]

        require(
            not missing,
            "Missing required files:\n" + "\n".join(missing),
        )

        print(f"FOUND: {len(REQUIRED_FILES)} files")
        print("PASS")
        passed += 1

        # ------------------------------------------------------------
        # TEST 2
        # ------------------------------------------------------------
        print("\nTEST 2: Python compilation")

        for relative in REQUIRED_FILES:
            py_compile.compile(
                str(BASE / relative),
                doraise=True,
            )

        print(f"COMPILED: {len(REQUIRED_FILES)} files")
        print("PASS")
        passed += 1

        # ------------------------------------------------------------
        # TEST 3
        # ------------------------------------------------------------
        print("\nTEST 3: Critical source structure")

        checks = {
            "main_ui.py": ("QApplication", "LunaWindow"),
            "core/agent.py": ("LunaAgent", "def shutdown"),
            "core/barge_in.py": ("BargeInListener", "def start", "def stop"),
            "core/stop_control.py": ("GenerationGuard",),
            "ui/window.py": ("LunaWindow", "closeEvent"),
            "ui/voice_worker.py": ("VoiceWorker", "_on_barge_stop"),
            "voice/speech_to_text.py": ("SpeechToText", "def _transcribe"),
            "voice/text_to_speech.py": ("TextToSpeech", "def stop"),
            "browser/browser_controller.py": ("BrowserController",),
        }

        for relative, terms in checks.items():
            source = (BASE / relative).read_text(
                encoding="utf-8",
            )
            for term in terms:
                require(
                    term in source,
                    f"{term!r} missing from {relative}",
                )

        print("PASS")
        passed += 1

        # ------------------------------------------------------------
        # TEST 4
        # ------------------------------------------------------------
        print("\nTEST 4: Runtime dependency imports")

        for label, module_name in IMPORTS:
            try:
                importlib.import_module(module_name)
            except Exception as error:
                raise AssertionError(
                    f"{label} import failed: {error}"
                ) from error

            print(f"{label}: PASS")

        print("PASS")
        passed += 1

        # ------------------------------------------------------------
        # TEST 5
        # ------------------------------------------------------------
        print("\nTEST 5: Application entry-point contract")

        main_source = (
            BASE / "main_ui.py"
        ).read_text(encoding="utf-8")

        require(
            re.search(
                r"if\s+__name__\s*==\s*[\"']__main__[\"']",
                main_source,
            )
            is not None,
            "main_ui.py has no __main__ entry point",
        )

        require(
            "QApplication" in main_source,
            "QApplication missing",
        )

        require(
            "LunaWindow" in main_source,
            "LunaWindow missing",
        )

        require(
            ".show()" in main_source,
            "Window show() missing",
        )

        require(
            ".exec()" in main_source
            or ".exec_()" in main_source,
            "Qt event loop missing",
        )

        print("PASS")
        passed += 1

        # ------------------------------------------------------------
        # TEST 6
        # ------------------------------------------------------------
        print("\nTEST 6: Package hygiene / secret scan")

        source_files = list(
            BASE.rglob("*.py")
        )

        ignored_parts = {
            "__pycache__",
            ".git",
            "backup_phase14_5",
        }

        findings = []

        for path in source_files:

            if any(
                part in ignored_parts
                for part in path.parts
            ):
                continue

            try:
                source = path.read_text(
                    encoding="utf-8"
                )
            except UnicodeDecodeError:
                continue

            for pattern in SECRET_PATTERNS:

                if re.search(pattern, source):
                    findings.append(
                        str(path.relative_to(BASE))
                    )
                    break

        require(
            not findings,
            "Possible hard-coded API secret found in:\n"
            + "\n".join(findings),
        )

        print(
            f"SCANNED: {len(source_files)} Python files"
        )
        print("NO OBVIOUS HARD-CODED API KEYS: PASS")
        print("PASS")
        passed += 1

        # ------------------------------------------------------------
        # TEST 7
        # ------------------------------------------------------------
        print("\nTEST 7: Project metadata / deployment readiness")

        icon_candidates = (
            BASE / "logo.ico",
            BASE / "assets" / "logo.ico",
            BASE / "ui" / "logo.ico",
        )

        icon_found = next(
            (
                path for path in icon_candidates
                if path.is_file()
            ),
            None,
        )

        if icon_found:
            print(
                f"ICON: {icon_found.relative_to(BASE)}"
            )
        else:
            print(
                "ICON: not found "
                "(optional, but recommended for Windows release)"
            )

        for directory in (
            "core",
            "ui",
            "voice",
            "nlp",
            "browser",
            "tools",
            "web",
        ):
            init_file = BASE / directory / "__init__.py"
            require(
                init_file.is_file(),
                f"Missing package marker: {directory}\\__init__.py",
            )

        print("PACKAGE MARKERS: PASS")
        print("PASS")
        passed += 1

        # ------------------------------------------------------------
        # TEST 8
        # ------------------------------------------------------------
        print("\nTEST 8: Deployment tool availability")

        tools = []

        try:
            importlib.import_module("PyInstaller")
            tools.append("PyInstaller")
        except Exception:
            pass

        pyside6_deploy = (
            Path(sys.executable).resolve().parent
            / "pyside6-deploy.exe"
        )

        if pyside6_deploy.exists():
            tools.append("pyside6-deploy")

        require(
            bool(tools),
            "Neither PyInstaller nor pyside6-deploy was found. "
            "Install a deployment tool before building.",
        )

        print(
            "AVAILABLE: " + ", ".join(tools)
        )
        print("PASS")
        passed += 1

        # ------------------------------------------------------------
        # TEST 9
        # ------------------------------------------------------------
        print("\nTEST 9: Deployment configuration surface")

        config_source = (
            BASE / "config.py"
        ).read_text(
            encoding="utf-8"
        )

        require(
            "GROQ_API_KEY" in config_source
            or "GROQ" in config_source,
            "Groq configuration surface not found",
        )

        print("CONFIG SURFACE: PASS")
        passed += 1

        # ------------------------------------------------------------
        # FINAL
        # ------------------------------------------------------------

        print()
        print("=" * 78)
        print(
            f"✅ PHASE 14.7 PREFLIGHT PASSED "
            f"({passed}/9)"
        )
        print("=" * 78)
        print(
            "Next: build a Windows release package and test the packaged app."
        )

        return 0

    except Exception as error:

        print()
        print("=" * 78)
        print("❌ PHASE 14.7 PREFLIGHT FAILED")
        print("=" * 78)
        print(f"ERROR: {error}")
        print()

        return 1


if __name__ == "__main__":
    raise SystemExit(run())