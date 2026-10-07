from nlp.planner import LunaPlanner
from core.action_executor import ActionExecutor


planner = LunaPlanner()


tests = [
    "open chrome and go to youtube",

    "open notepad and type hello Luna",

    "take a screenshot and show system information",

    "open YouTube and search for Python tutorials",

    "open YouTube, search for Python tutorials and open the first result",
]


print()
print("=" * 80)
print("             🌙 LUNA PLANNER + EXECUTOR TEST")
print("=" * 80)


for number, command in enumerate(
    tests,
    start=1
):

    print()
    print("=" * 80)
    print(f"TEST {number}")
    print(f"USER: {command}")
    print("=" * 80)

    # ========================================================
    # STEP 1 - CREATE PLAN
    # ========================================================

    print()
    print("[1] Creating plan...")

    plan = planner.create_plan(
        command
    )

    print()
    print("[PLANNER] Generated plan:")

    print(
        plan
    )

    actions = plan.get(
        "actions",
        []
    )

    if not actions:

        print(
            "❌ Planner returned no actions."
        )

        continue

    print()
    print("[PLANNER] Actions:")

    for index, action in enumerate(
        actions,
        start=1
    ):

        print(
            f"{index}. "
            f"{action.get('action')} "
            f"-> "
            f"target={action.get('target')} "
            f"text={action.get('text')}"
        )

    # ========================================================
    # STEP 2 - EXECUTE PLAN
    # ========================================================

    print()
    print("[2] Executing plan...")
    print()

    def progress_callback(
        step,
        total,
        action,
        result
    ):

        print()
        print(
            f"✅ EXECUTION "
            f"{step}/{total}"
        )

        print(
            f"Action: {action}"
        )

        print(
            f"Result: {result}"
        )

    results = ActionExecutor.execute(
        plan,
        progress_callback=progress_callback
    )

    # ========================================================
    # STEP 3 - FINAL RESULTS
    # ========================================================

    print()
    print("[3] Final execution results:")

    if not results:

        print(
            "❌ Nothing was executed."
        )

    else:

        for result in results:

            print(
                f"Step {result['step']}: "
                f"{result['result']}"
            )


print()
print("=" * 80)
print("                 ✅ ALL TESTS FINISHED")
print("=" * 80)