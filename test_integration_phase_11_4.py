import threading
import time

from core.agent import LunaAgent


def run_in_thread(agent, message):
    box = {"response": None, "error": None}

    def worker():
        try:
            box["response"] = agent.chat(message, model="groq")
        except Exception as exc:
            box["error"] = exc

    thread = threading.Thread(
        target=worker,
        name="LUNA-Integration-Worker",
        daemon=True,
    )
    thread.start()
    thread.join()

    return box["response"], box["error"]


def run_test(agent, name, message, threaded=False):
    print()
    print("=" * 78)
    print(f"TEST: {name}")
    print(f"USER: {message}")
    print("=" * 78)

    started = time.perf_counter()

    try:
        if threaded:
            response, error = run_in_thread(agent, message)
            if error is not None:
                raise error
        else:
            response = agent.chat(message, model="groq")

        elapsed = time.perf_counter() - started
        print("SUCCESS: True")
        print(f"TIME: {elapsed:.3f}s")
        print(f"LUNA: {response}")

        return True, elapsed, str(response)

    except Exception as exc:
        elapsed = time.perf_counter() - started
        print("SUCCESS: False")
        print(f"TIME: {elapsed:.3f}s")
        print(f"ERROR: {exc}")

        return False, elapsed, str(exc)


def main():
    print("=" * 78)
    print("🌙 LUNA PHASE 11.4 - FULL INTEGRATION TEST")
    print("=" * 78)

    agent = LunaAgent()

    router_tests = (
        ("File", "Luna, find agent.py", "file"),
        ("Computer", "Luna, open Calculator", "computer"),
        ("Browser", "Luna, open YouTube", "browser"),
        ("Web", "Luna, latest AI news", "web"),
        ("AI", "Luna, explain machine learning", "ai"),
    )

    print()
    print("=" * 78)
    print("FAST ROUTER CHECK")
    print("=" * 78)

    router_passed = 0

    for name, message, expected in router_tests:
        try:
            value = agent.fast_router.route(message)

            if isinstance(value, str):
                actual = value.strip().lower()
            elif isinstance(value, dict):
                actual = str(
                    value.get(
                        "route",
                        value.get("category", "ai"),
                    )
                ).strip().lower()
            else:
                actual = str(value).strip().lower()

            ok = actual == expected

            print(
                f"{'PASS' if ok else 'FAIL'} | "
                f"{name:9} | expected={expected:8} | actual={actual}"
            )

            if ok:
                router_passed += 1

        except Exception as exc:
            print(f"FAIL | {name:9} | ERROR={exc}")

    tests = [
        ("File Intelligence", "Luna, find agent.py", False),
        ("Computer Control", "Luna, open Calculator", False),

        ("Browser open - thread 1", "Luna, open YouTube", True),
        ("YouTube search - thread 2", "Luna, search YouTube for AI tutorials", True),
        ("YouTube search - thread 3", "Luna, search YouTube for Python tutorials", True),
        ("Browser back - thread 4", "Luna, go back", True),
        ("Browser open - thread 5", "Luna, open YouTube", True),

        ("Web / Tavily", "Luna, latest AI news", False),
        ("Normal AI", "Luna, explain machine learning in one sentence", False),
    ]

    passed = 0
    results = []

    for name, message, threaded in tests:
        ok, elapsed, output = run_test(
            agent,
            name,
            message,
            threaded=threaded,
        )

        results.append((name, ok, elapsed, output))

        if ok:
            passed += 1

        if threaded:
            time.sleep(0.5)

    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print(f"FastRouter: {router_passed}/{len(router_tests)} passed")
    print(f"Integration: {passed}/{len(tests)} passed")

    for name, ok, elapsed, output in results:
        print(
            f"{'PASS' if ok else 'FAIL':4} | "
            f"{name:34} | {elapsed:.3f}s"
        )

    if router_passed == len(router_tests) and passed == len(tests):
        print()
        print("[LUNA] Shutting down browser worker cleanly...")
        agent.shutdown()
        print("[LUNA] Browser worker shutdown complete.")
        print()
        print("=" * 78)
        print("✅ PHASE 11.4 PASSED")
        print("=" * 78)
        return 0

    print()
    agent.shutdown()
    print("=" * 78)
    print("⚠ PHASE 11.4 NEEDS REVIEW")
    print("=" * 78)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())