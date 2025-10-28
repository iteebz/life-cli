import re
from datetime import timedelta
from sqlite3 import IntegrityError

from ..api import (
    add_tag,
    complete_item,
    delete_item,
    get_items_by_tag,
    is_repeating,
    remove_tag,
    toggle_focus,
    uncomplete_item,
    update_item,
)
from ..api.checks import add_check, delete_check
from ..api.dashboard import get_pending_items, get_today_completed
from ..lib import clock
from ..lib.ansi import ANSI
from ..lib.match import _find_by_partial, find_item
from ..lib.render import render_item_list


def complete(partial: str) -> str | None:
    """Complete an item or record a check for repeating item (fuzzy match)."""
    item = find_item(partial)
    if item:
        if is_repeating(item.id):
            try:
                add_check(item.id)
            except IntegrityError:
                return f"Already checked: {item.content}"
        else:
            complete_item(item.id)
        return item.content
    return None


def uncomplete(partial: str) -> str | None:
    """Mark completed item as incomplete (fuzzy match)."""
    item = _find_by_partial(partial, get_today_completed())
    if item:
        uncomplete_item(item.id)
        return item.content
    return None


def toggle_complete(
    partial: str, date: str | None = None, undo: bool = False
) -> tuple[str, str] | None:
    """Toggle completion status on item (fuzzy match)."""
    if undo:
        # Try to find in completed items
        # This needs to be broader than just today, but for now, we'll use get_today_completed
        # as it's what's currently available and used for uncomplete logic.
        completed_items = get_today_completed()
        item = _find_by_partial(partial, completed_items)
        if item:
            item_id = item.id
            if is_repeating(item_id):
                delete_check(item_id, check_date=date)
                return "Pending", item.content
            uncomplete_item(item_id)
            return "Pending", item.content
    else:
        # Try to find in pending items
        pending_item = find_item(partial)
        if pending_item:
            item_id = pending_item.id
            if is_repeating(item_id):
                try:
                    add_check(item_id, check_date=date)
                    return "Checked", pending_item.content
                except IntegrityError:
                    return "Already checked", pending_item.content
            complete_item(item_id, completed_date=date)
            return "Done", pending_item.content
    return None


def toggle(partial: str) -> tuple[str, str] | None:
    """Toggle focus on item (tasks only, not repeating items)."""
    item = find_item(partial)
    if item and not item.is_repeat:
        new_focus = toggle_focus(item.id, item.focus)
        status = "Focused" if new_focus else "Unfocused"
        return status, item.content
    return None


def update(partial: str, **kwargs) -> str | None:
    """Update item (focus/due only on tasks, not repeating items)."""
    item = find_item(partial)
    if item:
        if any(k in kwargs for k in ("focus", "due")) and item.is_repeat:
            return None
        update_item(item.id, **kwargs)
        return kwargs.get("content", item.content)
    return None


def remove(partial: str) -> str | None:
    """Remove item (LIFO - most recent match)."""
    pending = get_pending_items(asc=False)
    item = _find_by_partial(partial, pending)
    if item:
        delete_item(item.id)
        return item.content

    completed_today = get_today_completed()
    item = _find_by_partial(partial, completed_today)
    if item:
        delete_item(item.id)
        return item.content

    return None


def _parse_due_date(date_input: str) -> str | None:
    """Parse flexible date input to YYYY-MM-DD format.

    Accepts:
    - today, tomorrow
    - Day names (mon, tue, wed, thu, fri, sat, sun) - finds next occurrence
    - ISO format (YYYY-MM-DD)
    """
    date_input = date_input.lower().strip()
    today = clock.today()

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

    if item.is_repeat:
        return f"Cannot set due date on repeating items: {item.content}"

    if remove:
        update_item(item.id, due=None)
        return f"Due date removed: {item.content}"

    if not date_str:
        return "Due date required (today, tomorrow, day name, or YYYY-MM-DD) or use -r/--remove to clear"

    update_item(item.id, due=date_str)
    return f"Due: {item.content} on {date_str}"


def edit_item(new_content, partial) -> str:
    """Edit item content. Returns message string."""
    result = update(partial, content=new_content)
    if result:
        return f"Updated: {result} → {new_content}"
    return f"No match for: {partial}"


def manage_tag(tag_name, item_partial=None, remove=False, include_completed=False):
    """Add, remove, or view items by tag (fuzzy match)"""
    if item_partial:
        item = None
        if include_completed:
            all_items = get_pending_items() + get_today_completed()
            item = _find_by_partial(item_partial, all_items)
        else:
            item = find_item(item_partial)

        if item:
            if remove:
                remove_tag(item.id, tag_name)
                return f"Untagged: {item.content} ← {ANSI.GREY}#{tag_name}{ANSI.RESET}"
            add_tag(item.id, tag_name)
            return f"Tagged: {item.content} {ANSI.GREY}#{tag_name} {ANSI.RESET}"
        return f"No match for: {item_partial}"
    items = get_items_by_tag(tag_name)
    if items:
        return f"\n{tag_name.upper()} ({len(items)}):\n{render_item_list(items)}"
    return f"No items tagged with #{tag_name}"
