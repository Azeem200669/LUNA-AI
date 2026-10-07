"""
🌙 LUNA PHASE 14.6 - FINAL STARTUP / SHUTDOWN TEST

This test launches the real PySide6 application surface without a visible GUI,
verifies the window can be constructed and shown, then closes it and verifies
that the application lifecycle releases its owned resources.

No microphone, AI request, or live voice mode is started.
"""
from __future__ import annotations

import ast
import os
import sys
import time
import traceback
from pathlib import Path

# Keep the test isolated from the user's desktop while still creating a real
# QApplication + LunaWindow object.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

BASE = Path(__file__).resolve().parent
if (BASE / "core").is_dir():
    PROJECT_ROOT = BASE
else:
    PROJECT_ROOT = Path.cwd()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    print("=" * 78)
    print("🌙 LUNA PHASE 14.6 - FINAL STARTUP / SHUTDOWN TEST")
    print("=" * 78)
    print(f"PROJECT ROOT: {PROJECT_ROOT}")
    print(f"QT PLATFORM: {os.environ.get('QT_QPA_PLATFORM')}")

    started_all = time.perf_counter()
    app = None
    window = None
    original_agent_shutdown = None
    shutdown_called = False

    try:
        # ================================================================
        # TEST 1: Required application files
        # ================================================================
        print("\nTEST 1: Application files")
        required = (
            "main_ui.py",
            "ui/window.py",
            "ui/voice_worker.py",
            "core/agent.py",
            "core/action_executor.py",
            "voice/text_to_speech.py",
        )
        missing = [p for p in required if not (PROJECT_ROOT / p).is_file()]
        require(not missing, "Missing files:\n" + "\n".join(missing))
        print(f"FOUND: {len(required)} files")
        print("PASS")

        # ================================================================
        # TEST 2: Syntax / entry-point contracts
        # ================================================================
        print("\nTEST 2: Python syntax + entry-point contracts")

        main_source = (PROJECT_ROOT / "main_ui.py").read_text(encoding="utf-8")
        window_source = (PROJECT_ROOT / "ui" / "window.py").read_text(encoding="utf-8")

        for name in ("QApplication", "LunaWindow"):
            require(name in main_source, f"main_ui.py missing {name}")

        require(".show()" in main_source, "main_ui.py does not show LunaWindow")
        require(
            ".exec()" in main_source or ".exec_()" in main_source,
            "main_ui.py does not enter QApplication event loop",
        )

        tree = ast.parse(window_source, filename="ui/window.py")
        defined = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        }

        require("LunaWindow" in defined, "LunaWindow class missing")
        require("closeEvent" in defined, "closeEvent missing")
        print("PASS")

        # ================================================================
        # TEST 3: Shutdown ownership contracts
        # ================================================================
        print("\nTEST 3: Shutdown ownership contracts")

        # The closeEvent must explicitly release the agent, because LunaAgent
        # owns the browser worker and persistent memory.
        require(
            "self.agent.shutdown()" in window_source,
            "LunaWindow.closeEvent() does not call self.agent.shutdown()",
        )

        agent_source = (PROJECT_ROOT / "core" / "agent.py").read_text(encoding="utf-8")

        for term in (
            "def shutdown(self):",
            "worker.shutdown()",
            "self.memory.close()",
        ):
            require(term in agent_source, f"core/agent.py missing {term}")

        print("PASS")

        # ================================================================
        # TEST 4: QApplication creation
        # ================================================================
        print("\nTEST 4: QApplication startup")

        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv[:1])

        require(app is not None, "QApplication creation failed")

        print("QAPPLICATION: READY")
        print("PASS")

        # ================================================================
        # TEST 5: Real LunaWindow construction
        # ================================================================
        print("\nTEST 5: LunaWindow construction")

        started = time.perf_counter()

        from ui.window import LunaWindow

        window = LunaWindow()

        construction_time = time.perf_counter() - started

        require(window is not None, "LunaWindow construction returned None")
        require(
            window.windowTitle() == "LUNA - Personal AI Assistant",
            f"Unexpected title: {window.windowTitle()}",
        )
        require(hasattr(window, "agent"), "LunaWindow.agent missing")
        require(hasattr(window, "core"), "LunaWindow.core missing")
        require(hasattr(window, "conversation"), "Conversation panel missing")
        require(hasattr(window, "chat_input"), "ChatInput missing")

        print(f"TIME: construction = {construction_time:.3f}s")
        print(f"TITLE: {window.windowTitle()}")
        print("PASS")

        # ================================================================
        # TEST 6: Show + event-loop processing
        # ================================================================
        print("\nTEST 6: Window show + event processing")

        window.show()

        # Give Qt a few event turns. QTest is not required for this test.
        for _ in range(5):
            app.processEvents()
            time.sleep(0.05)

        require(window.isVisible(), "LunaWindow did not become visible")
        require(
            window.status.text() == "● ONLINE",
            f"Unexpected initial status: {window.status.text()}",
        )

        print("WINDOW: VISIBLE")
        print(f"STATUS: {window.status.text()}")
        print("PASS")

        # ================================================================
        # TEST 7: Initial worker state is clean
        # ================================================================
        print("\nTEST 7: Initial worker state")

        require(window.ai_worker is None, "AI worker unexpectedly active")
        require(window.tts_worker is None, "TTS worker unexpectedly active")
        require(window.voice_worker is None, "Voice worker unexpectedly active")

        print("AI WORKER: None")
        print("TTS WORKER: None")
        print("VOICE WORKER: None")
        print("PASS")

        # ================================================================
        # TEST 8: Real closeEvent -> agent shutdown callback
        # ================================================================
        print("\nTEST 8: Window close -> agent shutdown")

        original_agent_shutdown = window.agent.shutdown

        def tracked_shutdown():
            nonlocal shutdown_called
            shutdown_called = True
            print("[TEST] agent.shutdown() called")
            return original_agent_shutdown()

        # Instance attribute replacement is intentionally used only for this
        # test so we can verify the window actually invokes its owned agent.
        window.agent.shutdown = tracked_shutdown

        started = time.perf_counter()

        window.close()

        for _ in range(20):
            app.processEvents()
            if not window.isVisible():
                break
            time.sleep(0.05)

        close_time = time.perf_counter() - started

        require(not window.isVisible(), "LunaWindow remained visible after close()")
        require(
            shutdown_called,
            "LunaWindow.closeEvent() did not call agent.shutdown()",
        )

        print(f"TIME: close = {close_time:.3f}s")
        print("WINDOW: CLOSED")
        print("AGENT SHUTDOWN: CALLED")
        print("PASS")

        # ================================================================
        # TEST 9: Browser worker + memory final state
        # ================================================================
        print("\nTEST 9: Final resource state")

        browser_worker = getattr(window.agent, "_browser_worker", None)

        if browser_worker is not None:
            require(
                not browser_worker._thread.is_alive(),
                "Browser worker thread is still alive after application close",
            )

        require(
            getattr(window.agent, "_shutdown_complete", False),
            "LunaAgent did not mark shutdown complete",
        )

        print("BROWSER WORKER: STOPPED")
        print("AGENT SHUTDOWN COMPLETE: True")
        print("PASS")

        # ================================================================
        # TEST 10: QApplication quit
        # ================================================================
        print("\nTEST 10: QApplication shutdown")

        app.quit()
        app.processEvents()

        print("QAPPLICATION: QUIT REQUESTED")
        print("PASS")

        total = time.perf_counter() - started_all

        print()
        print("=" * 78)
        print("✅ PHASE 14.6 FINAL STARTUP / SHUTDOWN PASSED")
        print(f"TOTAL TIME: {total:.3f}s")
        print("=" * 78)

        return 0

    except Exception as error:

        print()
        print("=" * 78)
        print("❌ PHASE 14.6 FAILED")
        print("=" * 78)
        print(f"ERROR: {error}")
        print()
        traceback.print_exc()
        return 1

    finally:
        # Defensive cleanup if an assertion occurs mid-test.
        try:
            if window is not None and window.isVisible():
                window.close()
        except Exception:
            pass

        try:
            if app is not None:
                app.quit()
                app.processEvents()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())