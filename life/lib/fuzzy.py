from collections.abc import Sequence
from difflib import get_close_matches
from typing import TypeVar

from ..models import Habit, Task

__all__ = ["find_in_pool"]

FUZZY_MATCH_CUTOFF = 0.8

T = TypeVar("T", Task, Habit)


def _match_uuid_prefix(partial: str, pool: Sequence[T]) -> T | None:
    """Match item by UUID prefix (first 8 chars)."""
    partial_lower = partial.lower()
    for item in pool:
        if item.id[:8].startswith(partial_lower):
            return item
    return None


def _match_substring(partial: str, pool: Sequence[T]) -> T | None:
    """Match item by substring in content."""
    partial_lower = partial.lower()
    for item in pool:
        if partial_lower in item.content.lower():
            return item
    return None


def _match_fuzzy(partial: str, pool: Sequence[T]) -> T | None:
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


def _find_by_partial(partial: str, pool: Sequence[T]) -> T | None:
    """Find item in pool: UUID prefix, substring, fuzzy match."""
    if not pool:
        return None
    return (
        _match_uuid_prefix(partial, pool)
        or _match_substring(partial, pool)
        or _match_fuzzy(partial, pool)
    )


def find_in_pool(partial: str, pool: Sequence[T]) -> T | None:
    """Public entry point: find item in an arbitrary pool."""
    return _find_by_partial(partial, pool)
