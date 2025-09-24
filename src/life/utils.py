from difflib import get_close_matches
from datetime import date
from .storage import get_pending_tasks, complete_task, toggle_focus, update_task


def find_task_by_partial(partial):
    """Find task by fuzzy matching partial string"""
    pending = get_pending_tasks()
    if not pending:
        return None
    
    contents = [task[1] for task in pending]
    matches = get_close_matches(partial.lower(), [c.lower() for c in contents], n=1, cutoff=0.3)
    
    if not matches:
        return None
    
    match_content = matches[0]
    for task in pending:
        if task[1].lower() == match_content:
            return task
    
    return None


def complete_task_fuzzy(partial):
    """Complete task using fuzzy matching"""
    task = find_task_by_partial(partial)
    if task:
        complete_task(task[0])
        return task[1]
    return None


def toggle_focus_fuzzy(partial):
    """Toggle focus on task using fuzzy matching"""
    task = find_task_by_partial(partial)
    if task:
        new_focus = toggle_focus(task[0], task[3])
        status = "Focused" if new_focus else "Unfocused"
        return status, task[1]
    return None, None


def update_task_fuzzy(partial, content=None, due=None, focus=None):
    """Update task using fuzzy matching"""
    task = find_task_by_partial(partial)
    if task:
        update_task(task[0], content=content, due=due, focus=focus)
        # Return the new content value or the original if not updated
        updated_content = content if content is not None else task[1]
        return updated_content
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
    else:
        return f"(overdue: {abs(diff)} days)"