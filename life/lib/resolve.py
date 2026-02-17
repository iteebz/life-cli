from ..models import Habit, Task
from .errors import exit_error

__all__ = ["resolve_task", "resolve_habit", "resolve_item"]


def resolve_task(ref: str) -> Task:
    from ..tasks import find_task

    task = find_task(ref)
    if not task:
        exit_error(f"No task found: '{ref}'")
    return task


def resolve_habit(ref: str) -> Habit:
    from ..habits import find_habit

    habit = find_habit(ref)
    if not habit:
        exit_error(f"No habit found: '{ref}'")
    return habit


def resolve_item(ref: str) -> tuple[Task | None, Habit | None]:
    from ..habits import find_habit
    from ..tasks import find_task, find_task_any

    task = find_task(ref)
    habit = find_habit(ref) if not task else None
    if not task and not habit:
        task = find_task_any(ref)
        habit = find_habit(ref) if not task else None
    if not task and not habit:
        exit_error(f"No item found: '{ref}'")
    return task, habit
