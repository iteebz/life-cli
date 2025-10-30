from ..api.checks import add_check, delete_check
from ..api.tasks import update_task
from ..lib import clock
from .fuzzy import find_habit, find_task


def toggle_focus(task_id: str, current_focus: bool) -> tuple[str, str]:
    """Toggles the focus status of a task."""
    new_focus = not current_focus
    updated = update_task(task_id, focus=new_focus)
    status_text = "Focused" if new_focus else "Unfocused"
    return status_text, updated.content if updated else ""


def toggle_done(
    partial: str, date: str | None = None, undo: bool = False
) -> tuple[str, str] | None:
    """Toggle completion status on task or habit (fuzzy match)."""
    task = find_task(partial)
    if task:
        if undo:
            from .. import db

            with db.get_db() as conn:
                conn.execute("UPDATE tasks SET completed = NULL WHERE id = ?", (task.id,))
        else:
            update_task(task.id, completed=clock.today().isoformat())
        return task.content, "undone" if undo else "done"

    habit = find_habit(partial)
    if habit:
        if undo:
            delete_check(habit.id, clock.today().isoformat())
        else:
            add_check(habit.id, clock.today().isoformat())
        return habit.content, "undone" if undo else "done"

    return None
