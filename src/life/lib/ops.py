import re
from datetime import date, timedelta

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
from ..core.tag import get_tags
from .match import _find_by_partial, find_item
from .store import _CLEAR


def _is_task_like(iid: str) -> bool:
    """Check if item supports focus/due (not habit/chore)."""
    tags = get_tags(iid)
    return not any(tag in ("habit", "chore") for tag in tags)


def complete(partial: str) -> str | None:
    """Complete or check item."""
    item = find_item(partial)
    if item:
        if is_repeating(item[0]):
            check_repeat(item[0])
        else:
            complete_item(item[0])
        return item[1]
    return None


def uncomplete(partial: str) -> str | None:
    """Uncomplete item."""
    item = _find_by_partial(partial, get_today_completed())
    if item:
        uncomplete_item(item[0])
        return item[1]
    return None


def toggle(partial: str) -> tuple[str, str] | None:
    """Toggle focus on item (tasks only, not habits/chores)."""
    item = find_item(partial)
    if item and _is_task_like(item[0]):
        new_focus = toggle_focus(item[0], item[2])
        status = "Focused" if new_focus else "Unfocused"
        return status, item[1]
    return None


def update(partial: str, content=None, due=_CLEAR, focus=None) -> str | None:
    """Update item (focus/due only on tasks, not habits/chores)."""
    item = find_item(partial)
    if item:
        if (focus is not None or due is not _CLEAR) and not _is_task_like(item[0]):
            return None
        update_item(item[0], content=content, due=due, focus=focus)
        return content if content is not None else item[1]
    return None


def remove(partial: str) -> str | None:
    """Remove item (LIFO - most recent match).

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


def _parse_due_date(date_input: str) -> str | None:
    """Parse flexible date input to YYYY-MM-DD format.

    Accepts:
    - today, tomorrow
    - Day names (mon, tue, wed, thu, fri, sat, sun) - finds next occurrence
    - ISO format (YYYY-MM-DD)
    """
    date_input = date_input.lower().strip()
    today = date.today()

    if date_input == "today":
        return today.isoformat()

    if date_input == "tomorrow":
        return (today + timedelta(days=1)).isoformat()

    day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
    if date_input in day_map:
        target_day = day_map[date_input]
        current_day = today.weekday()
        days_ahead = target_day - current_day
        if days_ahead <= 0:
            days_ahead += 7
        return (today + timedelta(days=days_ahead)).isoformat()

    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_input):
        return date_input

    return None


def set_due(args, remove=False) -> str:
    """Set or remove due date. Returns message string."""
    if not args:
        return "Due date and item required"

    date_str = None
    item_args = args

    if not remove and len(args) > 0:
        parsed = _parse_due_date(args[0])
        if parsed:
            date_str = parsed
            item_args = args[1:]

    if not item_args:
        return "Item name required"

    partial = " ".join(item_args)
    item = find_item(partial)
    if not item:
        return f"No match for: {partial}"

    if not _is_task_like(item[0]):
        return f"Cannot set due date on habits/chores: {item[1]}"

    if remove:
        update_item(item[0], due=None)
        return f"Due date removed: {item[1]}"

    if not date_str:
        return "Due date required (today, tomorrow, day name, or YYYY-MM-DD) or use -r/--remove to clear"

    update_item(item[0], due=date_str)
    return f"Due: {item[1]} on {date_str}"


def edit_item(new_content, partial) -> str:
    """Edit item content. Returns message string."""
    result = update(partial, content=new_content)
    if result:
        return f"Updated: {result} → {new_content}"
    return f"No match for: {partial}"
