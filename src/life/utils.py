from datetime import date
from difflib import get_close_matches

from .storage import (
    check_reminder,
    complete_task,
    delete_task,
    get_pending_tasks,
    toggle_focus,
    update_task,
)


def find_task(partial, category=None):
    """Find task by fuzzy matching partial string"""
    pending = get_pending_tasks()
    if not pending:
        return None

    # Filter by category if specified
    if category:
        pending = [task for task in pending if task[2] == category]

    partial_lower = partial.lower()

    # First: exact substring matches
    for task in pending:
        if partial_lower in task[1].lower():
            return task

    # Fallback: fuzzy matching with high threshold
    contents = [task[1] for c in pending]
    matches = get_close_matches(partial_lower, [c.lower() for c in contents], n=1, cutoff=0.8)

    if matches:
        match_content = matches[0]
        for task in pending:
            if task[1].lower() == match_content:
                return task

    return None


def complete_fuzzy(partial, category=None):
    """Complete task or check reminder using fuzzy matching"""
    task = find_task(partial, category=category)
    if task:
        if category == "reminder":
            check_reminder(task[0])
        else:
            complete_task(task[0])
        return task[1]
    return None


def toggle_fuzzy(partial):
    """Toggle focus on task using fuzzy matching"""
    task = find_task(partial)
    if task:
        new_focus = toggle_focus(task[0], task[3])
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
    """Format due date with relative day difference for backlog only"""
    if not due_date_str:
        return ""

    due = date.fromisoformat(due_date_str)
    today = date.today()
    diff = (due - today).days

    if diff > 0:
        return f"(due: {diff} days)"
    return f"(overdue: {abs(diff)} days)"
