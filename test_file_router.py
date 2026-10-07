import time

from core.file_router import FileRouter


router = FileRouter()


tests = [

    "Luna, find agent.py",

    "Luna, find my Python files",

    "Luna, show me the files in Downloads",

    "Luna, what files are in my Downloads folder",

    "Luna, find PDF files in Downloads",

    "Luna, open agent.py",

    "Luna, find files containing voice",

    "Luna, open the latest PDF in Downloads",

    "Luna, find files containing browser",

    "Luna, find test_planner.py",

    "Luna, open test_planner.py",

    "Luna, show files in my LUNA project",

]


print()
print("=" * 85)
print("             🌙 LUNA FAST FILE ROUTER TEST")
print("=" * 85)


for index, command in enumerate(
    tests,
    start=1
):

    print()
    print("=" * 85)

    print(
        f"TEST {index}"
    )

    print(
        f"USER: {command}"
    )

    print("=" * 85)

    start_time = time.perf_counter()

    result = router.handle(
        command
    )

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print()
    print(
        "HANDLED:",
        result["handled"]
    )

    print(
        "SUCCESS:",
        result["success"]
    )

    print(
        "OPERATION:",
        result["operation"]
    )

    print(
        "LANGUAGE:",
        result["language"]
    )

    print(
        f"EXECUTION TIME: {elapsed:.4f} seconds"
    )

    print()
    print(
        "🤖 LUNA:"
    )

    print(
        result["answer"]
    )

    if result["results"]:

        print()
        print(
            "RESULTS:"
        )

        for item in result["results"][:10]:

            print(
                f"- {item['name']}"
            )

            print(
                f"  {item['path']}"
            )

    if result["error"]:

        print()
        print(
            "ERROR:",
            result["error"]
        )


print()
print("=" * 85)
print("              ✅ FAST FILE TEST COMPLETE")
print("=" * 85)