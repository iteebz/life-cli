from datetime import timedelta

from .config import get_profile, set_profile
from .dashboard import get_pending_items, get_today_breakdown, get_today_completed
from .habits import (
    add_habit,
    delete_habit,
    find_habit,
    get_checks,
    get_habits,
    toggle_check,
    update_habit,
)
from .lib.ansi import ANSI
from .lib.backup import backup as backup_life
from .lib.clock import today
from .lib.dates import add_date, list_dates, parse_due_date, remove_date
from .lib.errors import echo, exit_error
from .lib.format import format_habit, format_status, format_task
from .lib.parsing import parse_due_and_item, validate_content
from .lib.render import render_dashboard, render_habit_matrix, render_momentum
from .models import Habit, Task
from .momentum import weekly_momentum
from .tags import add_tag, remove_tag
from .tasks import (
    add_task,
    delete_task,
    find_task,
    find_task_any,
    get_tasks,
    toggle_completed,
    toggle_focus,
    update_task,
)


def _parse_time(time_str: str) -> str:
    """Parse HH:MM or H:MM, return HH:MM or raise ValueError."""
    import re
    time_str = time_str.strip().lower()
    m = re.match(r'^(\d{1,2}):(\d{2})$', time_str)
    if m:
        h, mn = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mn <= 59:
            return f"{h:02d}:{mn:02d}"
    raise ValueError(f"Invalid time '{time_str}' — use HH:MM")

__all__ = [
    "cmd_dashboard",
    "cmd_task",
    "cmd_habit",
    "cmd_done",
    "cmd_rm",
    "cmd_focus",
    "cmd_due",
    "cmd_rename",
    "cmd_tag",
    "cmd_habits",
    "cmd_profile",
    "cmd_dates",
    "cmd_status",
    "cmd_backup",
    "cmd_momentum",
    "cmd_today",
    "cmd_tomorrow",
    "cmd_schedule",
]


def _require_task(partial: str) -> Task:
    task = find_task(partial)
    if not task:
        exit_error(f"No task found matching '{partial}'")
    return task


def _require_item(partial: str) -> tuple[Task | None, Habit | None]:
    task = find_task(partial)
    habit = find_habit(partial) if not task else None
    if not task and not habit:
        task = find_task_any(partial)
        habit = find_habit(partial) if not task else None
    if not task and not habit:
        exit_error(f"No item found matching '{partial}'")
    return task, habit


def cmd_dashboard(verbose: bool = False) -> None:
    items = get_pending_items() + get_habits()
    today_items = get_today_completed()
    today_breakdown = get_today_breakdown()
    echo(render_dashboard(items, today_breakdown, None, None, today_items, verbose=verbose))


def cmd_task(
    content_args: list[str],
    focus: bool = False,
    due: str | None = None,
    tags: list[str] | None = None,
    under: str | None = None,
) -> None:
    content = " ".join(content_args) if content_args else ""
    try:
        validate_content(content)
    except ValueError as e:
        exit_error(f"Error: {e}")
    resolved_due = parse_due_date(due) if due else None
    parent_id = None
    if under:
        parent_task = find_task(under)
        if not parent_task:
            exit_error(f"No task found matching '{under}'")
        if parent_task.parent_id:
            exit_error("Error: subtasks cannot have subtasks")
        parent_id = parent_task.id
    task_id = add_task(content, focus=focus, due=resolved_due, tags=tags, parent_id=parent_id)
    symbol = f"{ANSI.BOLD}⦿{ANSI.RESET}" if focus else "□"
    prefix = "  └ " if parent_id else ""
    echo(f"{prefix}{format_status(symbol, content, task_id)}")


def cmd_habit(content_args: list[str], tags: list[str] | None = None) -> None:
    content = " ".join(content_args) if content_args else ""
    try:
        validate_content(content)
    except ValueError as e:
        exit_error(f"Error: {e}")
    habit_id = add_habit(content, tags=tags)
    echo(format_status("□", content, habit_id))


def cmd_done(args: list[str]) -> None:
    partial = " ".join(args) if args else ""
    if not partial:
        exit_error("Usage: life done <item>")
    task, habit = _require_item(partial)

    if habit:
        today_date = today()
        checks = get_checks(habit.id)
        is_undo_action = today_date in checks
        toggle_check(habit.id)
        checked = not is_undo_action
        echo(format_habit(habit, checked=checked))
    elif task:
        toggle_completed(task.id)
        echo(format_task(task))


def cmd_rm(args: list[str]) -> None:
    partial = " ".join(args) if args else ""
    if not partial:
        exit_error("Usage: life rm <item>")
    task = find_task(partial)
    habit = find_habit(partial) if not task else None
    if task:
        delete_task(task.id)
        echo(f"{ANSI.DIM}{task.content}{ANSI.RESET}")
    elif habit:
        delete_habit(habit.id)
        echo(f"{ANSI.DIM}{habit.content}{ANSI.RESET}")
    else:
        exit_error(f"No match for: {partial}")


def cmd_focus(args: list[str]) -> None:
    partial = " ".join(args) if args else ""
    if not partial:
        exit_error("Usage: life focus <item>")
    task = _require_task(partial)
    toggle_focus(task.id)
    symbol = f"{ANSI.BOLD}⦿{ANSI.RESET}" if not task.focus else "□"
    echo(format_status(symbol, task.content))


def cmd_due(args: list[str], remove: bool = False) -> None:
    try:
        date_str, item_name = parse_due_and_item(args, remove=remove)
    except ValueError as e:
        exit_error(str(e))
    task = _require_task(item_name)
    if remove:
        update_task(task.id, due=None)
        echo(format_status("□", task.content))
    elif date_str:
        update_task(task.id, due=date_str)
        echo(format_status(f"{ANSI.GREY}{date_str.split('-')[2]}d:{ANSI.RESET}", task.content))
    else:
        exit_error(
            "Due date required (today, tomorrow, day name, or YYYY-MM-DD) or use -r/--remove to clear"
        )


def cmd_rename(from_args: list[str], to_content: str) -> None:
    if not to_content:
        exit_error("Error: 'to' content cannot be empty.")
    partial_from = " ".join(from_args) if from_args else ""
    task = find_task(partial_from)
    habit = find_habit(partial_from) if not task else None
    item_to_rename = task or habit
    if not item_to_rename:
        exit_error(f"No fuzzy match found for: '{partial_from}'")
    if item_to_rename.content == to_content:
        exit_error(f"Error: Cannot rename '{item_to_rename.content}' to itself.")
    if isinstance(item_to_rename, Task):
        update_task(item_to_rename.id, content=to_content)
    else:
        update_habit(item_to_rename.id, content=to_content)
    echo(f"Updated: '{item_to_rename.content}' → '{to_content}'")


def cmd_tag(
    tag_name: str | None,
    args: list[str] | None,
    tag_opt: str | None = None,
    remove: bool = False,
) -> None:
    if tag_opt:
        tag_name_final = tag_opt
        positionals = ([tag_name] if tag_name else []) + (args or [])
        item_partial = " ".join(positionals)
    else:
        if not tag_name or not args:
            exit_error(
                "Error: Missing arguments. Use `life tag TAG ITEM...` or `life tag ITEM... --tag TAG`."
            )
        tag_name_final = tag_name
        item_partial = " ".join(args)
    task = find_task(item_partial)
    habit = find_habit(item_partial) if not task else None
    if not task and not habit:
        task = find_task_any(item_partial)
        if not task:
            exit_error(f"No match for: {item_partial}")
    if task:
        if remove:
            remove_tag(task.id, None, tag_name_final)
            echo(f"{task.content} ← {ANSI.GREY}#{tag_name_final}{ANSI.RESET}")
        else:
            add_tag(task.id, None, tag_name_final)
            echo(f"{task.content} {ANSI.GREY}#{tag_name_final}{ANSI.RESET}")
    elif habit:
        if remove:
            remove_tag(None, habit.id, tag_name_final)
            echo(f"{habit.content} ← {ANSI.GREY}#{tag_name_final}{ANSI.RESET}")
        else:
            add_tag(None, habit.id, tag_name_final)
            echo(f"{habit.content} {ANSI.GREY}#{tag_name_final}{ANSI.RESET}")


def cmd_habits() -> None:
    echo(render_habit_matrix(get_habits()))


def cmd_profile(profile_text: str | None = None) -> None:
    if profile_text:
        set_profile(profile_text)
        echo(f"Profile set to: {profile_text}")
    else:
        echo(get_profile() or "No profile set")


def cmd_dates(
    action: str | None = None,
    name: str | None = None,
    date_str: str | None = None,
    emoji: str = "📌",
) -> None:
    if not action:
        dates_list = list_dates()
        if dates_list:
            for d in dates_list:
                echo(f"{d.get('emoji', '📌')} {d['name']} - {d['date']}")
        else:
            echo("No dates set")
        return
    if action == "add":
        if not name or not date_str:
            exit_error("Error: add requires name and date (YYYY-MM-DD)")
        add_date(name, date_str, emoji)
        echo(f"Added date: {emoji} {name} on {date_str}")
    elif action == "remove":
        if not name:
            exit_error("Error: remove requires a date name")
        remove_date(name)
        echo(f"Removed date: {name}")
    else:
        exit_error(
            f"Error: unknown action '{action}'. Use 'add', 'remove', or no argument to list."
        )


def cmd_status() -> None:
    tasks = get_tasks()
    habits = get_habits()
    today_date = today()

    untagged = [t for t in tasks if not t.tags]
    overdue = [t for t in tasks if t.due_date and t.due_date < today_date]
    jaynice = [t for t in tasks if "jaynice" in (t.tags or [])]
    focused = [t for t in tasks if t.focus]

    lines = []
    lines.append(f"tasks: {len(tasks)}  habits: {len(habits)}  focused: {len(focused)}")

    if overdue:
        lines.append(f"\nOVERDUE ({len(overdue)}):")
        for t in overdue:
            lines.append(f"  ! {t.content}")

    if untagged:
        lines.append(f"\nUNTAGGED ({len(untagged)}):")
        for t in untagged:
            lines.append(f"  ? {t.content}")

    if jaynice:
        lines.append(f"\nJAYNICE ({len(jaynice)}):")
        for t in jaynice:
            lines.append(f"  ♥ {t.content}")

    echo("\n".join(lines))


def cmd_backup() -> None:
    echo(str(backup_life()))


def cmd_momentum() -> None:
    echo(render_momentum(weekly_momentum()))


def _set_due_relative(args: list[str], offset_days: int, label: str) -> None:
    partial = " ".join(args) if args else ""
    if not partial:
        exit_error(f"Usage: life {label} <task>")
    task = _require_task(partial)
    due_str = (today() + timedelta(days=offset_days)).isoformat()
    update_task(task.id, due=due_str)
    echo(format_status("□", task.content))


def cmd_today(args: list[str]) -> None:
    _set_due_relative(args, 0, "today")


def cmd_tomorrow(args: list[str]) -> None:
    _set_due_relative(args, 1, "tomorrow")


def cmd_schedule(args: list[str], remove: bool = False) -> None:
    if not args:
        exit_error("Usage: life schedule <HH:MM> <task> | life schedule -r <task>")
    if remove:
        partial = " ".join(args)
        task = _require_task(partial)
        from . import db as _db
        with _db.get_db() as conn:
            conn.execute("UPDATE tasks SET scheduled_time = NULL WHERE id = ?", (task.id,))
        echo(format_status("□", task.content))
        return
    time_str = args[0]
    partial = " ".join(args[1:])
    if not partial:
        exit_error("Usage: life schedule <HH:MM> <task>")
    try:
        parsed = _parse_time(time_str)
    except ValueError as e:
        exit_error(str(e))
    task = _require_task(partial)
    update_task(task.id, scheduled_time=parsed)
    echo(format_status(f"{ANSI.GREY}{parsed}{ANSI.RESET}", task.content))
