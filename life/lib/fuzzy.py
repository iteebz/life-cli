from difflib import get_close_matches

from ..api.habits import get_all_habits
from ..api.models import Habit, Task
from ..api.tasks import get_all_tasks

MIN_UUID_PREFIX = 8
FUZZY_MATCH_CUTOFF = 0.8  # Minimum similarity score for fuzzy matching


def _match_uuid_prefix(partial: str, pool: list[Task | Habit]) -> Task | Habit | None:
    """Match item by UUID prefix."""
    if len(partial) < MIN_UUID_PREFIX:
        return None
    for item in pool:
        if item.id.startswith(partial):
            return item
    return None


def _match_substring(partial: str, pool: list[Task | Habit]) -> Task | Habit | None:
    """Match item by substring in content."""
    partial_lower = partial.lower()
    for item in pool:
        if partial_lower in item.content.lower():
            return item
    return None


def _match_fuzzy(partial: str, pool: list[Task | Habit]) -> Task | Habit | None:
    """Match item by fuzzy matching content."""
    partial_lower = partial.lower()
    contents = [item.content for item in pool]
    matches = get_close_matches(
        partial_lower, [c.lower() for c in contents], n=1, cutoff=FUZZY_MATCH_CUTOFF
    )
    if matches:
        match_content = matches[0]
        for item in pool:
            if item.content.lower() == match_content:
                return item
    return None


def _find_by_partial(partial: str, pool: list[Task | Habit]) -> Task | Habit | None:
    """Find item in pool: UUID prefix, substring, fuzzy match."""
    if not pool:
        return None
    return (
        _match_uuid_prefix(partial, pool)
        or _match_substring(partial, pool)
        or _match_fuzzy(partial, pool)
    )


def find_task(partial: str) -> Task | None:
    """Find task by fuzzy matching partial string or UUID prefix."""
    return _find_by_partial(partial, get_all_tasks())


def find_habit(partial: str) -> Habit | None:
    """Find habit by fuzzy matching partial string or UUID prefix."""
    return _find_by_partial(partial, get_all_habits())


def find_item(partial: str) -> Task | Habit | None:
    """Find any task or habit by fuzzy matching partial string or UUID prefix."""
    tasks = get_all_tasks()
    habits = get_all_habits()
    return _find_by_partial(partial, tasks + habits)
