from difflib import get_close_matches

from ..core.item import get_pending_items

MIN_UUID_PREFIX = 8
FUZZY_MATCH_THRESHOLD = 0.8


def _match_uuid_prefix(partial: str, pool: list[tuple]) -> tuple | None:
    """Match item by UUID prefix."""
    if len(partial) < MIN_UUID_PREFIX:
        return None
    for item in pool:
        if item[0].startswith(partial):
            return item
    return None


def _match_substring(partial: str, pool: list[tuple]) -> tuple | None:
    """Match item by substring in content."""
    partial_lower = partial.lower()
    for item in pool:
        if partial_lower in item[1].lower():
            return item
    return None


def _match_fuzzy(partial: str, pool: list[tuple]) -> tuple | None:
    """Match item by fuzzy matching content."""
    partial_lower = partial.lower()
    contents = [item[1] for item in pool]
    matches = get_close_matches(
        partial_lower, [c.lower() for c in contents], n=1, cutoff=FUZZY_MATCH_THRESHOLD
    )
    if matches:
        match_content = matches[0]
        for item in pool:
            if item[1].lower() == match_content:
                return item
    return None


def _find_by_partial(partial: str, pool: list[tuple]) -> tuple | None:
    """Find item in pool: UUID prefix, substring, fuzzy match."""
    if not pool:
        return None
    return (
        _match_uuid_prefix(partial, pool)
        or _match_substring(partial, pool)
        or _match_fuzzy(partial, pool)
    )


def find_item(partial: str) -> tuple | None:
    """Find item by fuzzy matching partial string or UUID prefix."""
    return _find_by_partial(partial, get_pending_items())
