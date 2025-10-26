from datetime import date, datetime
from difflib import get_close_matches

from .repeats import check_repeat
from .tasks import (
    complete_item,
    delete_item,
    get_pending_items,
    get_today_completed,
    toggle_focus,
    uncomplete_item,
    update_item,
    is_repeating,
)


def find_item(partial, tags_filter=None):
    """Find item by fuzzy matching partial string or UUID prefix"""
    pending = get_pending_items()
    if not pending:
        return None

    partial_lower = partial.lower()

    if len(partial) >= 8:
        for item in pending:
            if item[0].startswith(partial):
                return item

    for item in pending:
        if partial_lower in item[1].lower():
            return item

    contents = [item[1] for item in pending]
    matches = get_close_matches(partial_lower, [c.lower() for c in contents], n=1, cutoff=0.8)

    if matches:
        match_content = matches[0]
        for item in pending:
            if item[1].lower() == match_content:
                return item

    return None


def complete_fuzzy(partial):
    """Complete or check item using fuzzy matching"""
    item = find_item(partial)
    if item:
        if is_repeating(item[0]):
            check_repeat(item[0])
        else:
            complete_item(item[0])
        return item[1]
    return None


def uncomplete_fuzzy(partial):
    """Uncomplete item using fuzzy matching"""
    today_items = get_today_completed()

    if not today_items:
        return None

    partial_lower = partial.lower()

    for item in today_items:
        if partial_lower in item[1].lower():
            uncomplete_item(item[0])
            return item[1]

    contents = [item[1] for item in today_items]
    matches = get_close_matches(partial_lower, [c.lower() for c in contents], n=1, cutoff=0.8)

    if matches:
        match_content = matches[0]
        for item in today_items:
            if item[1].lower() == match_content:
                uncomplete_item(item[0])
                return item[1]

    return None


def toggle_fuzzy(partial):
    """Toggle focus on item using fuzzy matching"""
    item = find_item(partial)
    if item:
        new_focus = toggle_focus(item[0], item[2])
        status = "Focused" if new_focus else "Unfocused"
        return status, item[1]
    return None, None


def update_fuzzy(partial, content=None, due=None, focus=None):
    """Update item using fuzzy matching"""
    item = find_item(partial)
    if item:
        update_item(item[0], content=content, due=due, focus=focus)
        return content if content is not None else item[1]
    return None


def remove_fuzzy(partial):
    """Remove item using fuzzy matching"""
    item = find_item(partial)
    if item:
        delete_item(item[0])
        return item[1]
    return None


def delete_item_msg(partial):
    """Delete item. Returns message string."""
    removed = remove_fuzzy(partial)
    return f"Removed: {removed}" if removed else f"No match for: {partial}"


def toggle_focus_msg(partial):
    """Toggle focus. Returns message string."""
    status, content = toggle_fuzzy(partial)
    return f"{status}: {content}" if status else f"No match for: {partial}"


def format_due_date(due_date_str):
    """Format due date with relative day difference"""
    if not due_date_str:
        return ""

    due = date.fromisoformat(due_date_str)
    today = date.today()
    diff = (due - today).days

    if diff == 0:
        return "today:"
    if diff > 0:
        return f"{diff}d:"
    return f"{abs(diff)}d overdue:"


def format_decay(completed_str):
    """Format time since last checked as - Xd ago"""
    if not completed_str:
        return ""

    try:
        completed = datetime.fromisoformat(completed_str)
        now = datetime.now().astimezone()
        diff = now - completed

        days = diff.days
        hours = diff.seconds // 3600
        mins = (diff.seconds % 3600) // 60

        if days > 0:
            return f"- {days}d ago"
        if hours > 0:
            return f"- {hours}h ago"
        return f"- {mins}m ago"
    except Exception:
        return ""


def set_due(args, remove=False):
    """Set or remove due date. Returns message string."""
    import re
    
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
        else:
            if not date_str:
                return "Due date required (YYYY-MM-DD) or use -r/--remove to clear"
            update_item(item[0], due=date_str)
            return f"Due: {item[1]} on {date_str}"
    else:
        return f"No match for: {partial}"


def edit_item(new_content, partial):
    """Edit item content. Returns message string."""
    item = find_item(partial)
    if item:
        update_item(item[0], content=new_content)
        return f"Updated: {item[1]} → {new_content}"
    else:
        return f"No match for: {partial}"
