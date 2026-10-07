import time

from core.fast_router import FastRouter


router = FastRouter()


tests = [

    # FILE
    "Luna, find agent.py",
    "Luna, open test_planner.py",
    "Luna, find PDF files in Downloads",
    "Luna, show files in Downloads",
    "Luna, find files containing voice",

    # COMPUTER
    "Luna, open Chrome",
    "Luna, open Notepad",
    "Luna, take a screenshot",
    "Luna, increase volume",

    # BROWSER
    "Luna, go to YouTube",
    "Luna, search YouTube for Python tutorials",
    "Luna, open the first result",
    "Luna, go back",

    # WEB
    "Luna, what's the latest AI news?",
    "Luna, search the web for the latest Python news",

    # AI
    "Luna, explain quantum computing",
    "Luna, what is machine learning?",
]


print()
print("=" * 90)
print("                    🌙 LUNA FAST ROUTER TEST")
print("=" * 90)


times = []


for index, command in enumerate(
    tests,
    start=1
):

    start = time.perf_counter()

    result = router.route(
        command
    )

    elapsed = (
        time.perf_counter()
        - start
    ) * 1000

    times.append(
        elapsed
    )

    print()
    print("-" * 90)

    print(
        f"TEST {index}"
    )

    print(
        f"USER: {command}"
    )

    print()

    print(
        f"ROUTE:       {result['route']}"
    )

    print(
        f"CONFIDENCE:  {result['confidence']}"
    )

    print(
        f"REASON:      {result['reason']}"
    )

    print(
        f"ROUTING:     {elapsed:.3f} ms"
    )


print()
print("=" * 90)

print(
    f"AVERAGE ROUTING TIME: "
    f"{sum(times) / len(times):.3f} ms"
)

print(
    f"MAX ROUTING TIME: "
    f"{max(times):.3f} ms"
)

print(
    f"MIN ROUTING TIME: "
    f"{min(times):.3f} ms"
)

print("=" * 90)

print(
    "                     ✅ TEST COMPLETE"
)

print("=" * 90)