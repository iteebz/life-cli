from collections.abc import Sequence
from difflib import get_close_matches
from typing import TypeVar

from ..models import Habit, Task

__all__ = ["find_in_pool"]

FUZZY_MATCH_CUTOFF = 0.8

T = TypeVar("T", Task, Habit)


def _match_uuid_prefix(ref: str, pool: Sequence[T]) -> T | None:
    ref_lower = ref.lower()
    matches = [item for item in pool if item.id[:8].startswith(ref_lower)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        exact = next((item for item in matches if item.id == ref), None)
        if exact:
            return exact
        from .errors import exit_error

        sample = ", ".join(item.id[:8] for item in matches[:3])
        exit_error(f"Ambiguous ref '{ref}' matches multiple items: {sample}")
    return None


def _match_substring(ref: str, pool: Sequence[T]) -> T | None:
    ref_lower = ref.lower()
    exact = next((item for item in pool if item.content.lower() == ref_lower), None)
    if exact:
        return exact
    matches = [item for item in pool if ref_lower in item.content.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        from .errors import exit_error
        sample = ", ".join(f'"{item.content}"' for item in matches[:3])
        exit_error(f"Ambiguous match for '{ref}': {sample}")
    return None


def _match_fuzzy(ref: str, pool: Sequence[T]) -> T | None:
    ref_lower = ref.lower()
    contents = [item.content for item in pool]
    matches = get_close_matches(
        ref_lower, [c.lower() for c in contents], n=1, cutoff=FUZZY_MATCH_CUTOFF
    )
    if matches:
        match_content = matches[0]
        for item in pool:
            if item.content.lower() == match_content:
                return item
    return None


def find_in_pool(ref: str, pool: Sequence[T]) -> T | None:
    if not pool:
        return None
    return _match_uuid_prefix(ref, pool) or _match_substring(ref, pool) or _match_fuzzy(ref, pool)
