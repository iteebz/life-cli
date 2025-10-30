from ..api.tags import add_tag, get_habits_by_tag, get_tasks_by_tag, remove_tag
from ..api.tasks import delete_task, update_task
from ..lib.ansi import ANSI
from ..lib.dates import _parse_due_date
from ..lib.render import render_item_list
from ..ops.fuzzy import _find_by_partial, find_habit, find_task
from .dashboard import get_pending_items, get_today_completed


def update(partial: str, **kwargs) -> str | None:
    """Update task (focus/due only on tasks, not habits)."""
    task = find_task(partial)
    if task:
        if any(k in kwargs for k in ("focus", "due")):
            return None
        update_task(task.id, **kwargs)
        return kwargs.get("content", task.content)
    return None


def remove(partial: str) -> str | None:
    """Remove item (LIFO - most recent match)."""
    pending = get_pending_items(asc=False)
    task = _find_by_partial(partial, pending)
    if task:
        delete_task(task.id)
        return task.content

    completed_today = get_today_completed()
    item = _find_by_partial(partial, completed_today)
    if item:
        delete_task(item.id)
        return item.content

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
    task = find_task(partial)
    if not task:
        return f"No match for: {partial}"

    if remove:
        update_task(task.id, due=None)
        return f"Due date removed: {task.content}"

    if not date_str:
        return "Due date required (today, tomorrow, day name, or YYYY-MM-DD) or use -r/--remove to clear"

    update_task(task.id, due=date_str)
    return f"Due: {task.content} on {date_str}"


def edit_item(new_content, partial) -> str:
    """Edit item content. Returns message string."""
    result = update(partial, content=new_content)
    if result:
        return f"Updated: {result} → {new_content}"
    return f"No match for: {partial}"


def manage_tag(tag_name, item_partial=None, remove_t=False, include_completed=False):
    """Add, remove, or view items by tag (fuzzy match)"""
    if item_partial:
        task = find_task(item_partial)
        habit = find_habit(item_partial) if not task else None

        if task:
            if remove_t:
                remove_tag(task.id, None, tag_name)
                return f"Untagged: {task.content} ← {ANSI.GREY}#{tag_name}{ANSI.RESET}"

            add_tag(task.id, None, tag_name)
            return f"Tagged: {task.content} {ANSI.GREY}#{tag_name} {ANSI.RESET}"

        if habit:
            if remove_t:
                remove_tag(None, habit.id, tag_name)
                return f"Untagged: {habit.content} ← {ANSI.GREY}#{tag_name}{ANSI.RESET}"

            add_tag(None, habit.id, tag_name)
            return f"Tagged: {habit.content} {ANSI.GREY}#{tag_name} {ANSI.RESET}"

        return f"No match for: {item_partial}"

    tasks = get_tasks_by_tag(tag_name)
    habits = get_habits_by_tag(tag_name)
    items = tasks + habits
    if items:
        return f"\n{tag_name.upper()} ({len(items)}):\n{render_item_list(items)}"
    return f"No items tagged with #{tag_name}"
