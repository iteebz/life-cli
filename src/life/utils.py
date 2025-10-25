from datetime import date, datetime
from difflib import get_close_matches

from .repeats import check_repeat
from .tasks import (
    complete_task,
    delete_task,
    get_pending_tasks,
    get_today_completed,
    toggle_focus,
    uncomplete_task,
    update_task,
)


def find_task(partial, category=None):
    """Find task by fuzzy matching partial string or UUID prefix"""
    pending = get_pending_tasks()
    if not pending:
        return None

    # Filter by category if specified
    if category:
        pending = [task for task in pending if task[2] == category]

    partial_lower = partial.lower()

    # First: UUID prefix match (8+ chars)
    if len(partial) >= 8:
        for task in pending:
            if task[0].startswith(partial):
                return task

    # Second: exact substring matches on content
    for task in pending:
        if partial_lower in task[1].lower():
            return task

    # Fallback: fuzzy matching with high threshold
    contents = [task[1] for task in pending]
    matches = get_close_matches(partial_lower, [c.lower() for c in contents], n=1, cutoff=0.8)

    if matches:
        match_content = matches[0]
        for task in pending:
            if task[1].lower() == match_content:
                return task

    return None


def complete_fuzzy(partial, category=None):
    """Complete task or check repeat using fuzzy matching"""
    task = find_task(partial, category=category)
    if task:
        if category == "repeat":
            check_repeat(task[0])
        else:
            complete_task(task[0])
        return task[1]
    return None


def uncomplete_fuzzy(partial):
    """Uncomplete task using fuzzy matching"""
    today_items = get_today_completed()
    today_completed_tasks = [t for t in today_items if t[2] == "task"]

    if not today_completed_tasks:
        return None

    partial_lower = partial.lower()

    for task in today_completed_tasks:
        if partial_lower in task[1].lower():
            uncomplete_task(task[0])
            return task[1]

    from difflib import get_close_matches

    contents = [task[1] for task in today_completed_tasks]
    matches = get_close_matches(partial_lower, [c.lower() for c in contents], n=1, cutoff=0.8)

    if matches:
        match_content = matches[0]
        for task in today_completed_tasks:
            if task[1].lower() == match_content:
                uncomplete_task(task[0])
                return task[1]

    return None


def toggle_fuzzy(partial):
    """Toggle focus on task using fuzzy matching (tasks only)"""
    task = find_task(partial)
    if task:
        if task[2] != "task":
            return None, None
        new_focus = toggle_focus(task[0], task[3], category=task[2])
        status = "Focused" if new_focus else "Unfocused"
        return status, task[1]
    return None, None


def update_fuzzy(partial, content=None, due=None, focus=None):
    """Update task using fuzzy matching"""
    task = find_task(partial)
    if task:
        update_task(task[0], content=content, due=due, focus=focus)
        # Return the new content value or the original if not updated
        return content if content is not None else task[1]
    return None


def remove_fuzzy(partial):
    """Remove task using fuzzy matching"""
    task = find_task(partial)
    if task:
        delete_task(task[0])
        return task[1]
    return None


def format_due_date(due_date_str):
    """Format due date with relative day difference"""
    if not due_date_str:
        return ""

    due = date.fromisoformat(due_date_str)
    today = date.today()
    diff = (due - today).days

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
