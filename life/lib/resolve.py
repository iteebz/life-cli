from life.habits import find_habit, find_habit_exact
from life.models import Habit, Task
from life.tasks import find_task, find_task_any, find_task_exact

from .errors import exit_error

__all__ = [
    "resolve_habit",
    "resolve_item",
    "resolve_item_any",
    "resolve_item_exact",
    "resolve_task",
]


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


def _find_item(ref: str, find_task_fn) -> tuple[Task | None, Habit | None]:
    """Common logic for finding a task/habit pair."""
    task = find_task_fn(ref)
    habit = find_habit(ref) if not task else None
    return task, habit


def resolve_item(ref: str) -> tuple[Task | None, Habit | None]:
    task, habit = _find_item(ref, find_task)
    if not task and not habit:
        exit_error(f"No item found: '{ref}'")
    return task, habit


def resolve_item_any(ref: str) -> tuple[Task | None, Habit | None]:
    """Like resolve_item but falls back to completed tasks. Only for toggling done."""
    task, habit = _find_item(ref, find_task)
    if not task and not habit:
        task, _ = _find_item(ref, find_task_any)
    if not task and not habit:
        exit_error(f"No item found: '{ref}'")
    return task, habit


def resolve_item_exact(ref: str) -> tuple[Task | None, Habit | None]:
    """Like resolve_item but no fuzzy matching — exact/substring/UUID only."""
    task, habit = _find_item(ref, find_task_exact)
    if not task:
        habit = find_habit_exact(ref)
    if not task and not habit:
        exit_error(f"No item found: '{ref}'")
    return task, habit
