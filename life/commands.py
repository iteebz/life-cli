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
from .interventions import add_intervention, get_interventions
from .interventions import get_stats as get_intervention_stats
from .lib.ansi import ANSI
from .lib.backup import backup as backup_life
from .lib.clock import now, today
from .lib.dates import add_date, list_dates, parse_due_date, remove_date
from .lib.errors import echo, exit_error
from .lib.format import format_habit, format_status, format_task
from .lib.parsing import parse_due_and_item, parse_time, validate_content
from .lib.render import render_dashboard, render_habit_matrix, render_momentum
from .lib.resolve import resolve_item, resolve_item_any, resolve_task
from .metrics import build_feedback_snapshot, render_feedback_snapshot
from .models import Task
from .momentum import weekly_momentum
from .tags import add_tag, remove_tag
from .tasks import (
    add_task,
    delete_task,
    get_all_tasks,
    get_tasks,
    set_blocked_by,
    toggle_completed,
    toggle_focus,
    update_task,
)

__all__ = [
    "cmd_block",
    "cmd_dashboard",
    "cmd_list",
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
    "cmd_stats",
    "cmd_backup",
    "cmd_momentum",
    "cmd_now",
    "cmd_today",
    "cmd_tomorrow",
    "cmd_schedule",
    "cmd_steward",
    "cmd_track",
    "cmd_unblock",
]


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


def cmd_track(
    description: str | None = None,
    result: str | None = None,
    note: str | None = None,
    show_stats: bool = False,
    show_log: bool = False,
) -> None:
    if show_stats:
        stats = get_intervention_stats()
        total = sum(stats.values())
        if not total:
            echo("no interventions logged")
            return
        won = stats.get("won", 0)
        lost = stats.get("lost", 0)
        deferred = stats.get("deferred", 0)
        win_rate = int((won / total) * 100) if total else 0
        echo(
            f"won: {won}  lost: {lost}  deferred: {deferred}  total: {total}  win_rate: {win_rate}%"
        )
        return

    if show_log:
        interventions = get_interventions(20)
        if not interventions:
            echo("no interventions logged")
            return
        for i in interventions:
            ts = i.timestamp.strftime("%m-%d %H:%M")
            note_str = f"  ({i.note})" if i.note else ""
            echo(f"{ts}  {i.result:<8}  {i.description}{note_str}")
        return

    if not description or not result:
        exit_error("Usage: life track <description> --won|--lost|--deferred [--note 'text']")

    if result not in ("won", "lost", "deferred"):
        exit_error("Result must be --won, --lost, or --deferred")

    add_intervention(description, result, note)
    symbol = {"won": "✓", "lost": "✗", "deferred": "→"}[result]
    echo(f"{symbol} {description}")



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
    task, habit = resolve_item_any(ref)

    if habit:
        today_date = today()
        checks = get_checks(habit.id)
        is_undo_action = today_date in checks
        updated_habit = toggle_check(habit.id)
        checked = not is_undo_action
        echo(format_habit(updated_habit or habit, checked=checked))
    elif task:
        updated = toggle_completed(task.id)
        echo(format_task(updated or task))


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
    echo(format_status(symbol, task.content, task.id))


def cmd_due(args: list[str], remove: bool = False) -> None:
    try:
        date_str, item_name = parse_due_and_item(args, remove=remove)
    except ValueError as e:
        exit_error(str(e))
    task = resolve_task(item_name)
    if remove:
        update_task(task.id, due=None)
        echo(format_status("□", task.content, task.id))
    elif date_str:
        update_task(task.id, due=date_str)
        echo(format_status(f"{ANSI.GREY}{date_str.split('-')[2]}d:{ANSI.RESET}", task.content, task.id))
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
    echo(f"→ {to_content}")


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


def cmd_list() -> None:
    tasks = get_tasks()
    habits = get_habits()
    for t in tasks:
        tag_str = f"  {ANSI.GREY}#{' #'.join(t.tags)}{ANSI.RESET}" if t.tags else ""
        symbol = f"{ANSI.BOLD}⦿{ANSI.RESET}" if t.focus else "□"
        echo(f"{symbol} {t.content}{tag_str}")
    for h in habits:
        tag_str = f"  {ANSI.GREY}#{' #'.join(h.tags)}{ANSI.RESET}" if h.tags else ""
        echo(f"↻ {h.content}{tag_str}")


def cmd_status() -> None:
    tasks = get_tasks()
    all_tasks = get_all_tasks()
    habits = get_habits()
    today_date = today()

    untagged = [t for t in tasks if not t.tags]
    overdue = [t for t in tasks if t.due_date and t.due_date < today_date]
    jaynice = [t for t in tasks if "jaynice" in (t.tags or [])]
    focused = [t for t in tasks if t.focus]

    snapshot = build_feedback_snapshot(all_tasks=all_tasks, pending_tasks=tasks, today=today_date)

    lines = []
    lines.append(f"tasks: {len(tasks)}  habits: {len(habits)}  focused: {len(focused)}")
    lines.append("\nHEALTH:")
    lines.append(f"  untagged: {len(untagged)}")
    lines.append(f"  overdue: {len(overdue)}")
    lines.append(f"  jaynice_open: {len(jaynice)}")
    lines.append("\nFLAGS:")
    if snapshot.flags:
        lines.append("  " + ", ".join(snapshot.flags))
    else:
        lines.append("  none")
    lines.append("\nHOT LIST:")
    for t in overdue[:3]:
        lines.append(f"  ! {t.content}")
    for t in jaynice[:3]:
        lines.append(f"  ♥ {t.content}")

    if not overdue and not jaynice:
        lines.append("  none")

    echo("\n".join(lines))


def cmd_stats() -> None:
    tasks = get_tasks()
    all_tasks = get_all_tasks()
    today_date = today()
    snapshot = build_feedback_snapshot(all_tasks=all_tasks, pending_tasks=tasks, today=today_date)
    echo("\n".join(render_feedback_snapshot(snapshot)))


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
    echo(format_status("□", task.content, task.id))


def cmd_today(args: list[str]) -> None:
    _set_due_relative(args, 0, "today")


def cmd_tomorrow(args: list[str]) -> None:
    _set_due_relative(args, 1, "tomorrow")


def cmd_now(args: list[str]) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life now <task>")
    task = resolve_task(ref)
    current = now()
    due_str = today().isoformat()
    time_str = current.strftime("%H:%M")
    update_task(task.id, due=due_str, due_time=time_str)
    echo(format_status(f"{ANSI.GREY}{time_str}{ANSI.RESET}", task.content.lower(), task.id))


def cmd_schedule(args: list[str], remove: bool = False) -> None:
    if not args:
        exit_error("Usage: life schedule <HH:MM> <task> | life schedule -r <task>")
    if remove:
        task = resolve_task(" ".join(args))
        update_task(task.id, due_time=None)
        echo(format_status("□", task.content, task.id))
        return
    time_str = args[0]
    ref = " ".join(args[1:])
    if not ref:
        exit_error("Usage: life schedule <HH:MM> <task>")
    try:
        parsed = parse_time(time_str)
    except ValueError as e:
        exit_error(str(e))
    task = resolve_task(ref)
    update_task(task.id, due_time=parsed)
    echo(format_status(f"{ANSI.GREY}{parsed}{ANSI.RESET}", task.content, task.id))
