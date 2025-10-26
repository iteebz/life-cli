import re
from difflib import get_close_matches

from ..core.item import (
    complete_item,
    delete_item,
    get_pending_items,
    get_today_completed,
    is_repeating,
    toggle_focus,
    uncomplete_item,
    update_item,
)
from ..core.repeat import check_repeat

MIN_UUID_PREFIX = 8
FUZZY_MATCH_THRESHOLD = 0.8


def _find_by_partial(partial: str, pool: list[tuple]) -> tuple | None:
    """Find item in pool: UUID prefix, substring, fuzzy match."""
    if not pool:
        return None

    partial_lower = partial.lower()

    if len(partial) >= MIN_UUID_PREFIX:
        for item in pool:
            if item[0].startswith(partial):
                return item

    for item in pool:
        if partial_lower in item[1].lower():
            return item

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


def find_item(partial: str, tags_filter=None) -> tuple | None:
    """Find item by fuzzy matching partial string or UUID prefix"""
    return _find_by_partial(partial, get_pending_items())


def complete(partial: str) -> str | None:
    """Complete or check item"""
    item = find_item(partial)
    if item:
        if is_repeating(item[0]):
            check_repeat(item[0])
        else:
            complete_item(item[0])
        return item[1]
    return None


def uncomplete(partial: str) -> str | None:
    """Uncomplete item"""
    item = _find_by_partial(partial, get_today_completed())
    if item:
        uncomplete_item(item[0])
        return item[1]
    return None


def toggle(partial: str) -> tuple[str, str] | None:
    """Toggle focus on item"""
    item = find_item(partial)
    if item:
        new_focus = toggle_focus(item[0], item[2])
        status = "Focused" if new_focus else "Unfocused"
        return status, item[1]
    return None


def update(partial: str, content=None, due=None, focus=None) -> str | None:
    """Update item"""
    item = find_item(partial)
    if item:
        update_item(item[0], content=content, due=due, focus=focus)
        return content if content is not None else item[1]
    return None


def remove(partial: str) -> str | None:
    """Remove item (LIFO - most recent match)

    Searches: pending items, habits, chores, and completed items today
    """
    pending = get_pending_items(asc=False)

    item = _find_by_partial(partial, pending)
    if item:
        delete_item(item[0])
        return item[1]

    completed_today = get_today_completed()
    item = _find_by_partial(partial, completed_today)
    if item:
        delete_item(item[0])
        return item[1]

    return None


def set_due(args, remove=False):
    """Set or remove due date. Returns message string."""
    if not args:
        return "Due date and item required"

    date_str = None
    item_args = args

    if not remove and len(args) > 0 and re.match(r"^\d{4}-\d{2}-\d{2}$", args[0]):
        date_str = args[0]
        item_args = args[1:]

    if not item_args:
        return "Item name required"

    partial = " ".join(item_args)
    item = find_item(partial)
    if item:
        if remove:
            update_item(item[0], due=None)
            return f"Due date removed: {item[1]}"
        if not date_str:
            return "Due date required (YYYY-MM-DD) or use -r/--remove to clear"
        update_item(item[0], due=date_str)
        return f"Due: {item[1]} on {date_str}"
    return f"No match for: {partial}"


def edit_item(new_content, partial):
    """Edit item content. Returns message string."""
    result = update(partial, content=new_content)
    if result:
        return f"Updated: {result} → {new_content}"
    return f"No match for: {partial}"
