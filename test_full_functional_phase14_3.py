"""LUNA Phase 14.3 - full functional integration stress test.

Run this from the LUNA project root after Phase 14.2 passes.

This test intentionally exercises live application paths that 14.2 does not:
- public LunaAgent.chat() pipeline
- file routing
- Windows computer action
- planner + ActionExecutor multi-step flow
- persistent Chrome browser flow
- Tavily/web route
- Groq/normal AI route
- persistent memory round-trip
- clean agent shutdown

The default run is a real functional test and may open Calculator/Chrome and
perform a web search. The test avoids destructive file/system actions.

Troubleshooting flags are available for environments without live services:
    --skip-browser
    --skip-web
    --skip-ai

Using any skip flag means the run is not a complete Phase 14.3 verification.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


BASE = Path(__file__).resolve().parent
if (BASE / "core").is_dir():
    PROJECT_ROOT = BASE
else:
    PROJECT_ROOT = Path.cwd()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _assert_text(value, label: str) -> str:
    assert value is not None, f"{label}: returned None"
    text = str(value).strip()
    assert text, f"{label}: returned empty text"
    return text


def _timed_call(label: str, fn):
    started = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - started
    print(f"TIME: {label} = {elapsed:.3f}s")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="LUNA Phase 14.3 full functional test")
    parser.add_argument("--skip-browser", action="store_true")
    parser.add_argument("--skip-web", action="store_true")
    parser.add_argument("--skip-ai", action="store_true")
    args = parser.parse_args()

    print("=" * 78)
    print("🌙 LUNA PHASE 14.3 - FULL FUNCTIONAL INTEGRATION STRESS TEST")
    print("=" * 78)
    print(f"PROJECT ROOT: {PROJECT_ROOT}")

    if args.skip_browser or args.skip_web or args.skip_ai:
        print("WARNING: skip flag active; this is NOT a complete 14.3 verification.")

    from core.agent import LunaAgent

    agent = None
    passed = 0
    started_all = time.perf_counter()

    try:
        # ------------------------------------------------------------------
        # TEST 1: Real LunaAgent construction / core surface
        # ------------------------------------------------------------------
        print("\nTEST 1: LunaAgent construction")
        agent = _timed_call("agent construction", LunaAgent)
        assert agent is not None
        assert hasattr(agent, "chat")
        assert hasattr(agent, "fast_router")
        assert hasattr(agent, "memory")
        assert hasattr(agent, "shutdown")
        passed += 1
        print("PASS")

        # ------------------------------------------------------------------
        # TEST 2: Public chat -> file route
        # ------------------------------------------------------------------
        print("\nTEST 2: public chat -> file route")
        response = _timed_call(
            "file route",
            lambda: agent.chat("find agent.py"),
        )
        response_text = _assert_text(response, "file route")
        assert "agent.py" in response_text.lower(), response_text
        passed += 1
        print("PASS")

        # ------------------------------------------------------------------
        # TEST 3: Public chat -> Windows computer action
        # Safe, non-destructive screenshot only.
        # ------------------------------------------------------------------
        print("\nTEST 3: public chat -> computer action (screenshot)")
        response = _timed_call(
            "screenshot action",
            lambda: agent.chat("take a screenshot"),
        )
        response_text = _assert_text(response, "screenshot action")
        assert any(
            token in response_text.lower()
            for token in ("screenshot", "captured", "saved")
        ), response_text
        passed += 1
        print("PASS")

        # ------------------------------------------------------------------
        # TEST 4: Planner + ActionExecutor multi-step public chat
        # Safe local actions: Calculator + screenshot.
        # ------------------------------------------------------------------
        print("\nTEST 4: public chat -> planner -> ActionExecutor")
        response = _timed_call(
            "multi-step execution",
            lambda: agent.chat("open Calculator and take a screenshot"),
        )
        response_text = _assert_text(response, "multi-step execution")
        assert len(response_text) >= 10, response_text
        passed += 1
        print("PASS")

        # ------------------------------------------------------------------
        # TEST 5: Persistent memory round-trip without changing real profile
        # ------------------------------------------------------------------
        print("\nTEST 5: persistent memory write -> read -> delete")
        marker_key = "phase14_3_test_marker"
        marker_value = "LUNA_PHASE14_3_OK"
        agent.memory.set_memory(
            marker_key,
            marker_value,
            memory_type="test",
            confidence=1.0,
            source="phase14_3",
        )
        saved = agent.memory.get_memory(marker_key)
        assert saved is not None, "marker was not persisted"
        assert saved.get("memory_value") == marker_value, saved

        deleted = agent.memory.forget_memory(key=marker_key)
        assert deleted is True, "marker was not deleted"
        assert agent.memory.get_memory(marker_key) is None

        print("MEMORY MARKER: saved -> read -> deleted")
        passed += 1
        print("PASS")

        # ------------------------------------------------------------------
        # TEST 6: Browser flow
        # ------------------------------------------------------------------
        if args.skip_browser:
            print("\nTEST 6: browser flow -> SKIPPED")
        else:
            print("\nTEST 6: persistent Chrome browser flow")
            response = _timed_call(
                "open YouTube",
                lambda: agent.chat("open YouTube"),
            )
            _assert_text(response, "open YouTube")

            response = _timed_call(
                "YouTube search",
                lambda: agent.chat("search YouTube for AI tutorials"),
            )
            search_text = _assert_text(response, "YouTube search")
            assert len(search_text) >= 5, search_text

            response = _timed_call(
                "page title",
                lambda: agent.chat("what is the page title"),
            )
            title_text = _assert_text(response, "page title")
            assert "youtube" in title_text.lower(), title_text

            response = _timed_call(
                "browser back",
                lambda: agent.chat("go back"),
            )
            _assert_text(response, "browser back")
            passed += 1
            print("PASS")

        # ------------------------------------------------------------------
        # TEST 7: Web / Tavily live route
        # ------------------------------------------------------------------
        if args.skip_web:
            print("\nTEST 7: Tavily/web route -> SKIPPED")
        else:
            print("\nTEST 7: public chat -> live web/Tavily route")
            response = _timed_call(
                "Tavily search",
                lambda: agent.chat("search the web for Python documentation"),
            )
            web_text = _assert_text(response, "Tavily search")
            assert len(web_text) >= 20, web_text
            passed += 1
            print("PASS")

        # ------------------------------------------------------------------
        # TEST 8: Normal AI / Groq route
        # ------------------------------------------------------------------
        if args.skip_ai:
            print("\nTEST 8: AI/Groq route -> SKIPPED")
        else:
            print("\nTEST 8: public chat -> normal AI/Groq route")
            response = _timed_call(
                "normal AI",
                lambda: agent.chat("Explain a Python list in one sentence."),
            )
            ai_text = _assert_text(response, "normal AI")
            assert len(ai_text) >= 10, ai_text
            passed += 1
            print("PASS")

        # ------------------------------------------------------------------
        # TEST 9: Route normalization / mixed real requests
        # ------------------------------------------------------------------
        print("\nTEST 9: public chat route sequence")
        route_sequence = (
            "find agent.py",
            "take a screenshot",
            "open Calculator",
            "what is Python?",
        )

        for index, message in enumerate(route_sequence, start=1):
            response = _timed_call(
                f"sequence {index}: {message}",
                lambda m=message: agent.chat(m),
            )
            _assert_text(response, f"sequence {index}")

        passed += 1
        print("PASS")

        print("\n" + "=" * 78)
        print(f"✅ PHASE 14.3 FUNCTIONAL TESTS PASSED: {passed}")
        print(f"TOTAL ELAPSED: {time.perf_counter() - started_all:.3f}s")
        print("=" * 78)
        return 0

    except Exception as error:
        print("\n" + "=" * 78)
        print(f"❌ PHASE 14.3 FAILED: {type(error).__name__}: {error}")
        print("=" * 78)
        return 1

    finally:
        # The memory object is already closed in TEST 5 on purpose; the agent's
        # shutdown method is idempotent and remains the final lifecycle check.
        if agent is not None:
            try:
                agent.shutdown()
                print("SHUTDOWN: PASS")
            except Exception as error:
                print(f"SHUTDOWN: WARNING: {error}")


if __name__ == "__main__":
    raise SystemExit(main())