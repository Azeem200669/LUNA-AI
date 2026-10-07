"""
🌙 LUNA PHASE 14.4
BROWSER + FILE + COMPUTER STRESS TEST

Purpose:
- Stress FileRouter through public LunaAgent.chat()
- Stress computer actions through public LunaAgent.chat()
- Stress real Chrome browser flow through public LunaAgent.chat()
- Stress planner -> ActionExecutor
- Verify route switching does not break between subsystems
- Verify browser worker remains stable
- Verify agent shutdown completes cleanly

NO microphone
NO GUI launch
NO TTS
NO voice input

Real browser, screenshots, filesystem, and application actions are used.
"""

from __future__ import annotations

import os
import sys
import time
import traceback
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(
    r"C:\Users\shaik\Downloads\program\project\LUNA"
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORT
# ============================================================

try:
    from core.agent import LunaAgent
except Exception as error:
    print()
    print("=" * 78)
    print("IMPORT FAILURE")
    print("=" * 78)
    print(error)
    traceback.print_exc()
    raise


# ============================================================
# CONFIG
# ============================================================

SCREENSHOT_DIR = Path(
    r"C:\Users\shaik\OneDrive\Pictures\Screenshots"
)

FAILURE_WORDS = (
    "traceback",
    "exception",
    "error:",
    "failed",
    "couldn't complete",
    "could not complete",
)


# ============================================================
# HELPERS
# ============================================================

def timer():
    return time.perf_counter()


def elapsed(start):
    return time.perf_counter() - start


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def validate_response(response, label):
    """
    Basic public-chat contract validation.

    We intentionally do not require exact natural-language wording because
    the AI/router response text can legitimately vary.
    """

    require(
        response is not None,
        f"{label}: response is None",
    )

    require(
        isinstance(response, str),
        f"{label}: expected string response, got {type(response).__name__}",
    )

    require(
        response.strip() != "",
        f"{label}: response is empty",
    )

    lowered = response.lower()

    for bad_word in FAILURE_WORDS:
        require(
            bad_word not in lowered,
            f"{label}: suspicious failure response: {response}",
        )

    return response.strip()


def run_chat(agent, command, label):
    print()
    print("-" * 78)
    print(f"{label}")
    print(f"USER: {command}")
    print("-" * 78)

    started = timer()

    response = agent.chat(command)

    duration = elapsed(started)

    response = validate_response(
        response,
        label,
    )

    print(f"LUNA: {response}")
    print(f"TIME: {duration:.3f}s")

    return response, duration


# ============================================================
# MAIN TEST
# ============================================================

def main():

    print("=" * 78)
    print("🌙 LUNA PHASE 14.4 - BROWSER + FILE + COMPUTER STRESS TEST")
    print("=" * 78)
    print(f"PROJECT ROOT: {PROJECT_ROOT}")
    print()

    overall_start = timer()

    agent = None

    results = []

    try:

        # ====================================================
        # TEST 1
        # AGENT CONSTRUCTION
        # ====================================================

        print("=" * 78)
        print("TEST 1: LunaAgent construction")
        print("=" * 78)

        started = timer()

        agent = LunaAgent()

        duration = elapsed(started)

        print(f"TIME: agent construction = {duration:.3f}s")
        print("PASS")

        results.append(("TEST 1", True))


        # ====================================================
        # TEST 2
        # FILE ROUTER REPEATED OPERATIONS
        # ====================================================

        print()
        print("=" * 78)
        print("TEST 2: FileRouter repeated stress")
        print("=" * 78)

        file_commands = [
            "Luna, find agent.py",
            "Luna, find my Python files",
            "Luna, show me the files in Downloads",
            "Luna, find PDF files in Downloads",
            "Luna, find main_ui.py",
            "Luna, find config.py",
        ]

        file_count = 0
        file_total_time = 0.0

        # 5 complete rounds = 30 public chat calls.
        for round_no in range(1, 6):

            print()
            print(f"[FILE ROUND {round_no}/5]")

            for command in file_commands:

                response, duration = run_chat(
                    agent,
                    command,
                    f"FILE ROUND {round_no}: {command}",
                )

                file_count += 1
                file_total_time += duration

                require(
                    response,
                    "File response unexpectedly empty",
                )

        print()
        print(f"FILE OPERATIONS: {file_count}")
        print(f"FILE TOTAL TIME: {file_total_time:.3f}s")
        print(f"FILE AVG TIME: {file_total_time / file_count:.3f}s")
        print("PASS")

        results.append(("TEST 2", True))


        # ====================================================
        # TEST 3
        # COMPUTER SCREENSHOT STRESS
        # ====================================================

        print()
        print("=" * 78)
        print("TEST 3: Computer screenshot stress")
        print("=" * 78)

        SCREENSHOT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        before_files = {
            path.name
            for path in SCREENSHOT_DIR.glob("luna_screenshot_*.png")
        }

        screenshot_times = []

        for index in range(1, 8):

            command = "Luna, take a screenshot"

            response, duration = run_chat(
                agent,
                command,
                f"SCREENSHOT {index}/7",
            )

            screenshot_times.append(duration)

            require(
                "screenshot" in response.lower(),
                f"Screenshot response did not mention screenshot: {response}",
            )

        time.sleep(0.5)

        after_files = {
            path.name
            for path in SCREENSHOT_DIR.glob("luna_screenshot_*.png")
        }

        new_files = after_files - before_files

        print()
        print(f"SCREENSHOT OPERATIONS: {len(screenshot_times)}")
        print(
            f"SCREENSHOT AVG TIME: "
            f"{sum(screenshot_times) / len(screenshot_times):.3f}s"
        )
        print(f"NEW SCREENSHOT FILES: {len(new_files)}")

        require(
            len(new_files) >= 5,
            f"Expected at least 5 new screenshots, found {len(new_files)}",
        )

        print("PASS")

        results.append(("TEST 3", True))


        # ====================================================
        # TEST 4
        # COMPUTER APPLICATION CONTROL
        # ====================================================

        print()
        print("=" * 78)
        print("TEST 4: Computer application control stress")
        print("=" * 78)

        application_commands = [
            "Luna, open Calculator",
            "Luna, open Notepad",
            "Luna, open Calculator",
            "Luna, open Notepad",
        ]

        application_times = []

        for index, command in enumerate(
            application_commands,
            start=1,
        ):

            response, duration = run_chat(
                agent,
                command,
                f"APPLICATION {index}/{len(application_commands)}",
            )

            application_times.append(duration)

            require(
                "open" in response.lower()
                or "calculator" in response.lower()
                or "notepad" in response.lower(),
                f"Unexpected application response: {response}",
            )

        print()
        print(
            f"APPLICATION AVG TIME: "
            f"{sum(application_times) / len(application_times):.3f}s"
        )
        print("PASS")

        results.append(("TEST 4", True))


        # ====================================================
        # TEST 5
        # PLANNER -> ACTIONEXECUTOR
        # ====================================================

        print()
        print("=" * 78)
        print("TEST 5: Planner -> ActionExecutor repeated flow")
        print("=" * 78)

        planner_commands = [
            "Luna, open Calculator and take a screenshot",
            "Luna, open Calculator and take a screenshot",
            "Luna, open Calculator and take a screenshot",
        ]

        planner_times = []

        for index, command in enumerate(
            planner_commands,
            start=1,
        ):

            response, duration = run_chat(
                agent,
                command,
                f"PLANNER ROUND {index}/3",
            )

            planner_times.append(duration)

            lowered = response.lower()

            require(
                "calculator" in lowered
                or "opening" in lowered
                or "screenshot" in lowered,
                f"Planner response did not contain expected actions: {response}",
            )

        print()
        print(
            f"PLANNER AVG TIME: "
            f"{sum(planner_times) / len(planner_times):.3f}s"
        )
        print("PASS")

        results.append(("TEST 5", True))


        # ====================================================
        # TEST 6
        # BROWSER OPEN + SEARCH + TITLE + URL
        # ====================================================

        print()
        print("=" * 78)
        print("TEST 6: Persistent Chrome browser stress")
        print("=" * 78)

        browser_times = []

        browser_commands = [
            "Luna, open YouTube",
            "Luna, search YouTube for AI tutorials",
            "Luna, what is the page title",
            "Luna, what is the current URL",
            "Luna, go back",
            "Luna, go forward",
            "Luna, refresh",
        ]

        for index, command in enumerate(
            browser_commands,
            start=1,
        ):

            response, duration = run_chat(
                agent,
                command,
                f"BROWSER {index}/{len(browser_commands)}",
            )

            browser_times.append(duration)

            lowered = response.lower()

            if "page title" in command.lower():
                require(
                    "title" in lowered,
                    f"Title operation did not return title information: {response}",
                )

            elif "current url" in command.lower():
                require(
                    "url" in lowered
                    or "http" in lowered,
                    f"URL operation did not return URL information: {response}",
                )

        print()
        print(
            f"BROWSER AVG TIME: "
            f"{sum(browser_times) / len(browser_times):.3f}s"
        )
        print("PASS")

        results.append(("TEST 6", True))


        # ====================================================
        # TEST 7
        # BROWSER REPEATED SEARCH
        # ====================================================

        print()
        print("=" * 78)
        print("TEST 7: Browser repeated search stress")
        print("=" * 78)

        browser_searches = [
            "Luna, search YouTube for Python tutorials",
            "Luna, search YouTube for artificial intelligence",
            "Luna, search YouTube for machine learning",
        ]

        search_times = []

        for index, command in enumerate(
            browser_searches,
            start=1,
        ):

            response, duration = run_chat(
                agent,
                command,
                f"BROWSER SEARCH {index}/3",
            )

            search_times.append(duration)

            require(
                response.strip(),
                f"Browser search {index} returned empty response",
            )

        print()
        print(
            f"BROWSER SEARCH AVG TIME: "
            f"{sum(search_times) / len(search_times):.3f}s"
        )
        print("PASS")

        results.append(("TEST 7", True))


        # ====================================================
        # TEST 8
        # CROSS-SUBSYSTEM ROUTE SWITCHING
        # ====================================================

        print()
        print("=" * 78)
        print("TEST 8: File -> Computer -> Browser route switching")
        print("=" * 78)

        mixed_sequence = [
            ("Luna, find agent.py", "file"),
            ("Luna, take a screenshot", "computer"),
            ("Luna, open Calculator", "computer"),
            ("Luna, open YouTube", "browser"),
            ("Luna, search YouTube for AI tutorials", "browser"),
            ("Luna, find config.py", "file"),
            ("Luna, take a screenshot", "computer"),
            ("Luna, go back", "browser"),
            ("Luna, find main_ui.py", "file"),
            ("Luna, open Calculator", "computer"),
        ]

        mixed_times = []

        for index, (command, expected_area) in enumerate(
            mixed_sequence,
            start=1,
        ):

            response, duration = run_chat(
                agent,
                command,
                f"MIXED ROUTE {index}/{len(mixed_sequence)} [{expected_area}]",
            )

            mixed_times.append(duration)

            require(
                response.strip(),
                f"Mixed route operation {index} returned empty response",
            )

        print()
        print(
            f"MIXED ROUTE AVG TIME: "
            f"{sum(mixed_times) / len(mixed_times):.3f}s"
        )
        print("PASS")

        results.append(("TEST 8", True))


        # ====================================================
        # TEST 9
        # RAPID ROUTE ALTERNATION
        # ====================================================

        print()
        print("=" * 78)
        print("TEST 9: Rapid route alternation stress")
        print("=" * 78)

        rapid_sequence = [
            "Luna, find agent.py",
            "Luna, take a screenshot",
            "Luna, open Calculator",
            "Luna, what is the current URL",
            "Luna, find config.py",
            "Luna, take a screenshot",
            "Luna, go back",
            "Luna, find main_ui.py",
            "Luna, open Notepad",
            "Luna, take a screenshot",
        ]

        rapid_times = []

        rapid_start = timer()

        for index, command in enumerate(
            rapid_sequence,
            start=1,
        ):

            response, duration = run_chat(
                agent,
                command,
                f"RAPID {index}/{len(rapid_sequence)}",
            )

            rapid_times.append(duration)

            require(
                response.strip(),
                f"Rapid operation {index} returned empty response",
            )

        rapid_total = elapsed(rapid_start)

        print()
        print(f"RAPID OPERATIONS: {len(rapid_sequence)}")
        print(f"RAPID TOTAL TIME: {rapid_total:.3f}s")
        print(
            f"RAPID AVG TIME: "
            f"{sum(rapid_times) / len(rapid_times):.3f}s"
        )
        print("PASS")

        results.append(("TEST 9", True))


        # ====================================================
        # TEST 10
        # FINAL BROWSER STATE
        # ====================================================

        print()
        print("=" * 78)
        print("TEST 10: Final browser state verification")
        print("=" * 78)

        response_title, title_time = run_chat(
            agent,
            "Luna, what is the page title",
            "FINAL BROWSER TITLE",
        )

        require(
            "title" in response_title.lower(),
            f"Final title check failed: {response_title}",
        )

        response_url, url_time = run_chat(
            agent,
            "Luna, what is the current URL",
            "FINAL BROWSER URL",
        )

        require(
            "url" in response_url.lower()
            or "http" in response_url.lower(),
            f"Final URL check failed: {response_url}",
        )

        print()
        print(f"FINAL TITLE TIME: {title_time:.3f}s")
        print(f"FINAL URL TIME: {url_time:.3f}s")
        print("PASS")

        results.append(("TEST 10", True))


        # ====================================================
        # FINAL REPORT
        # ====================================================

        total_elapsed = elapsed(overall_start)

        passed = sum(
            1
            for _, status in results
            if status
        )

        print()
        print("=" * 78)
        print(f"✅ PHASE 14.4 FUNCTIONAL TESTS PASSED: {passed}/{len(results)}")
        print(f"TOTAL ELAPSED: {total_elapsed:.3f}s")
        print("=" * 78)

        require(
            passed == len(results),
            "One or more Phase 14.4 tests failed.",
        )

        return 0

    except Exception as error:

        print()
        print("=" * 78)
        print("❌ PHASE 14.4 FAILED")
        print("=" * 78)
        print(f"ERROR: {error}")
        print()
        traceback.print_exc()
        print("=" * 78)

        return 1

    finally:

        # ====================================================
        # CLEAN SHUTDOWN
        # ====================================================

        print()
        print("=" * 78)
        print("SHUTDOWN")
        print("=" * 78)

        if agent is not None:
            try:
                agent.shutdown()
                print("SHUTDOWN: PASS")
            except Exception as error:
                print(f"SHUTDOWN: FAIL -> {error}")
        else:
            print("SHUTDOWN: SKIPPED")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    raise SystemExit(main())