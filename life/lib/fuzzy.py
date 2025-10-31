from difflib import get_close_matches

from ..api.habits import get_habits
from models import Habit, Task
from ..api.tasks import get_tasks

FUZZY_MATCH_CUTOFF = 0.8


def _match_uuid_prefix(partial: str, pool: list[Task | Habit]) -> Task | Habit | None:
    """Match item by UUID prefix (first 8 chars)."""
    partial_lower = partial.lower()
    for item in pool:
        if item.id[:8].startswith(partial_lower):
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
    return _find_by_partial(partial, get_tasks())


def find_habit(partial: str) -> Habit | None:
    """Find habit by fuzzy matching partial string or UUID prefix."""
    return _find_by_partial(partial, get_habits())


def find_item(partial: str) -> tuple[Task | None, Habit | None]:
    """Find task or habit, return both results (one will be None). Useful for commands that work on both."""
    task = find_task(partial)
    habit = find_habit(partial) if not task else None
    return task, habit
