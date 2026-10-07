from nlp.planner import LunaPlanner
from core.action_executor import ActionExecutor


planner = LunaPlanner()

plan = planner.create_plan(
    "open notepad and type hello Luna"
)

print(plan)

results = ActionExecutor.execute(
    plan
)

print(results)