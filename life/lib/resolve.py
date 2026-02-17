from life.habits import find_habit
from life.models import Habit, Task
from life.tasks import find_task, find_task_any

from .errors import exit_error

__all__ = ["resolve_habit", "resolve_item", "resolve_item_any", "resolve_task"]


def resolve_task(ref: str) -> Task:
    task = find_task(ref)
    if not task:
        exit_error(f"No task found: '{ref}'")
    return task


def resolve_habit(ref: str) -> Habit:
    habit = find_habit(ref)
    if not habit:
        exit_error(f"No habit found: '{ref}'")
    return habit


def resolve_item(ref: str) -> tuple[Task | None, Habit | None]:
    task = find_task(ref)
    habit = find_habit(ref) if not task else None
    if not task and not habit:
        exit_error(f"No item found: '{ref}'")
    return task, habit


def resolve_item_any(ref: str) -> tuple[Task | None, Habit | None]:
    """Like resolve_item but falls back to completed tasks. Only for toggling done."""
    task = find_task(ref)
    habit = find_habit(ref) if not task else None
    if not task and not habit:
        task = find_task_any(ref)
    if not task and not habit:
        exit_error(f"No item found: '{ref}'")
    return task, habit
