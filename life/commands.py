from datetime import timedelta

from .config import get_profile, set_profile
from .dashboard import get_pending_items, get_today_breakdown, get_today_completed
from .habits import (
    add_habit,
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
from .lib.resolve import resolve_item, resolve_task
from .models import Habit, Task
from .momentum import weekly_momentum
from .tags import add_tag, remove_tag
from .tasks import (
    add_task,
    delete_task,
    get_tasks,
    set_blocked_by,
    toggle_completed,
    toggle_focus,
    update_task,
)


def cmd_block(blocked_args: list[str], blocker_args: list[str]) -> None:
    blocked_ref = " ".join(blocked_args)
    blocker_ref = " ".join(blocker_args)
    blocked = resolve_task(blocked_ref)
    blocker = resolve_task(blocker_ref)
    if blocker.id == blocked.id:
        exit_error("A task cannot block itself")
    set_blocked_by(blocked.id, blocker.id)
    echo(f"⊘ {blocked.content.lower()}  ←  {blocker.content.lower()}")


def cmd_unblock(args: list[str]) -> None:
    task = resolve_task(" ".join(args))
    if not task.blocked_by:
        exit_error(f"'{task.content}' is not blocked")
    set_blocked_by(task.id, None)
    echo(f"□ {task.content.lower()}  unblocked")


def cmd_steward() -> None:
    from pathlib import Path

    prompt_path = Path.home() / "life" / "STEWARD.md"
    if not prompt_path.exists():
        exit_error("STEWARD.md not found at ~/life/STEWARD.md")
    echo(prompt_path.read_text())


def _parse_time(time_str: str) -> str:
    import re

    time_str = time_str.strip().lower()
    m = re.match(r"^(\d{1,2}):(\d{2})$", time_str)
    if m:
        h, mn = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mn <= 59:
            return f"{h:02d}:{mn:02d}"
    raise ValueError(f"Invalid time '{time_str}' — use HH:MM")


__all__ = [
    "cmd_block",
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
    "cmd_steward",
    "cmd_unblock",
]


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
        parent_task = resolve_task(under)
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
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life done <item>")
    task, habit = resolve_item(ref)

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
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life rm <item>")
    task, habit = resolve_item(ref)
    if task:
        delete_task(task.id)
        echo(f"{ANSI.DIM}{task.content}{ANSI.RESET}")
    elif habit:
        from .habits import delete_habit
        delete_habit(habit.id)
        echo(f"{ANSI.DIM}{habit.content}{ANSI.RESET}")


def cmd_focus(args: list[str]) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life focus <item>")
    task = resolve_task(ref)
    toggle_focus(task.id)
    symbol = f"{ANSI.BOLD}⦿{ANSI.RESET}" if not task.focus else "□"
    echo(format_status(symbol, task.content))


def cmd_due(args: list[str], remove: bool = False) -> None:
    try:
        date_str, item_name = parse_due_and_item(args, remove=remove)
    except ValueError as e:
        exit_error(str(e))
    task = resolve_task(item_name)
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
    ref = " ".join(from_args) if from_args else ""
    task, habit = resolve_item(ref)
    item = task or habit
    if item.content == to_content:
        exit_error(f"Error: Cannot rename '{item.content}' to itself.")
    if isinstance(item, Task):
        update_task(item.id, content=to_content)
    else:
        update_habit(item.id, content=to_content)
    echo(f"Updated: '{item.content}' → '{to_content}'")


def cmd_tag(
    tag_name: str | None,
    args: list[str] | None,
    tag_opt: str | None = None,
    remove: bool = False,
) -> None:
    if tag_opt:
        tag_name_final = tag_opt
        positionals = ([tag_name] if tag_name else []) + (args or [])
        item_ref = " ".join(positionals)
    else:
        if not tag_name or not args:
            exit_error(
                "Error: Missing arguments. Use `life tag TAG ITEM...` or `life tag ITEM... --tag TAG`."
            )
        tag_name_final = tag_name
        item_ref = " ".join(args)
    task, habit = resolve_item(item_ref)
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
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error(f"Usage: life {label} <task>")
    task = resolve_task(ref)
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
        task = resolve_task(" ".join(args))
        from . import db as _db

        with _db.get_db() as conn:
            conn.execute("UPDATE tasks SET due_time = NULL WHERE id = ?", (task.id,))
        echo(format_status("□", task.content))
        return
    time_str = args[0]
    ref = " ".join(args[1:])
    if not ref:
        exit_error("Usage: life schedule <HH:MM> <task>")
    try:
        parsed = _parse_time(time_str)
    except ValueError as e:
        exit_error(str(e))
    task = resolve_task(ref)
    update_task(task.id, due_time=parsed)
    echo(format_status(f"{ANSI.GREY}{parsed}{ANSI.RESET}", task.content))
