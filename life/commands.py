import sys
import time
import shlex
import subprocess
from datetime import timedelta
from pathlib import Path

from .config import get_profile, set_profile
from .dashboard import get_pending_items, get_today_breakdown, get_today_completed
from .habits import (
    add_habit,
    archive_habit,
    delete_habit,
    get_archived_habits,
    get_checks,
    get_habits,
    toggle_check,
    update_habit,
)
from .interventions import (
    add_intervention,
    get_interventions,
)
from .interventions import (
    get_stats as get_intervention_stats,
)
from .lib.ansi import ANSI
from .lib.backup import backup as backup_life
from .lib.clock import now, today
from .lib.dates import add_date, list_dates, parse_due_date, remove_date
from .lib.errors import echo, exit_error
from .lib.format import format_status
from .lib.parsing import parse_due_and_item, parse_time, validate_content
from .lib.render import render_dashboard, render_habit_matrix, render_momentum, render_task_detail
from .lib.resolve import resolve_habit, resolve_item, resolve_item_any, resolve_item_exact, resolve_task
from .metrics import build_feedback_snapshot, render_feedback_snapshot
from .models import Task
from .momentum import weekly_momentum
from .tags import add_tag, remove_tag
from .tasks import (
    add_link,
    add_task,
    check_task,
    defer_task,
    delete_task,
    get_all_tasks,
    get_links,
    get_subtasks,
    get_tasks,
    remove_link,
    set_blocked_by,
    toggle_focus,
    uncheck_task,
    update_task,
)

__all__ = [
    "cmd_archive",
    "cmd_backup",
    "cmd_block",
    "cmd_check",
    "cmd_dashboard",
    "cmd_dates",
    "cmd_defer",
    "cmd_done",
    "cmd_due",
    "cmd_focus",
    "cmd_habit",
    "cmd_habits",
    "cmd_migrate",
    "cmd_momentum",
    "cmd_now",
    "cmd_profile",
    "cmd_rename",
    "cmd_rm",
    "cmd_schedule",
    "cmd_link",
    "cmd_unlink",
    "cmd_set",
    "cmd_show",
    "cmd_stats",
    "cmd_status",
    "cmd_steward",
    "cmd_tail",
    "cmd_tag",
    "cmd_task",
    "cmd_today",
    "cmd_tomorrow",
    "cmd_track",
    "cmd_unblock",
    "cmd_uncheck",
    "cmd_unfocus",
    "cmd_untag",
]


def _steward_prompt() -> str:
    prompt_path = Path.home() / "life" / "STEWARD.md"
    if not prompt_path.exists():
        exit_error("STEWARD.md not found at ~/life/STEWARD.md")
    return (
        prompt_path.read_text().strip()
        + "\n\nRun exactly one autonomous loop for ~/life. Make concrete progress, then stop."
    )


def cmd_tail(
    cycles: int = 1,
    interval_seconds: int = 0,
    model: str = "glm-5",
    dry_run: bool = False,
    continue_on_error: bool = False,
) -> None:
    if cycles < 1:
        exit_error("--cycles must be >= 1")
    if interval_seconds < 0:
        exit_error("--every must be >= 0")

    life_dir = Path.home() / "life"
    prompt = _steward_prompt()

    for i in range(1, cycles + 1):
        shell_cmd = (
            f"glm --print --model {shlex.quote(model)} -p {shlex.quote(prompt)}"
        )
        echo(f"[tail] cycle {i}/{cycles}  model={model}")
        if dry_run:
            echo(f"(cd {life_dir} && zsh -lic {shlex.quote(shell_cmd)})")
        else:
            result = subprocess.run(
                ["zsh", "-lic", shell_cmd],
                cwd=life_dir,
                check=False,
            )
            if result.returncode != 0:
                if continue_on_error:
                    echo(
                        f"[tail] cycle {i} failed (exit {result.returncode}), continuing"
                    )
                else:
                    exit_error(f"tail loop failed on cycle {i} (exit {result.returncode})")
        if i < cycles and interval_seconds > 0:
            echo(f"[tail] sleeping {interval_seconds}s")
            time.sleep(interval_seconds)


def cmd_set(
    args: list[str],
    parent: str | None = None,
    content: str | None = None,
    description: str | object = None,
) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life set <task> [-p parent] [-c content]")
    task = resolve_task(ref)
    updates: dict = {}
    if parent is not None:
        parent_task = resolve_task(parent)
        if parent_task.parent_id:
            exit_error("Error: subtasks cannot have subtasks")
        if parent_task.id == task.id:
            exit_error("Error: a task cannot be its own parent")
        if task.focus:
            exit_error("Error: cannot parent a focused task — unfocus first")
        updates["parent_id"] = parent_task.id
    if content is not None:
        if not content.strip():
            exit_error("Error: content cannot be empty")
        updates["content"] = content
    if description is not None:
        updates["description"] = description if description != "" else None
    if not updates:
        exit_error("Nothing to set. Use -p for parent, -c for content, or -d for description.")
    update_task(task.id, **updates)
    updated = resolve_task(content or ref)
    prefix = "  └ " if updated.parent_id else ""
    echo(f"{prefix}{format_status('□', updated.content, updated.id)}")


def cmd_show(args: list[str]) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life show <task>")
    task = resolve_task(ref)
    subtasks = get_subtasks(task.id)
    linked = get_links(task.id)
    echo(render_task_detail(task, subtasks, linked))


def cmd_link(a_args: list[str], b_args: list[str]) -> None:
    a = resolve_task(" ".join(a_args))
    b = resolve_task(" ".join(b_args))
    if a.id == b.id:
        exit_error("Cannot link a task to itself")
    add_link(a.id, b.id)
    echo(f"{a.content.lower()} {ANSI.GREY}~ {b.content.lower()}{ANSI.RESET}")


def cmd_unlink(a_args: list[str], b_args: list[str]) -> None:
    a = resolve_task(" ".join(a_args))
    b = resolve_task(" ".join(b_args))
    remove_link(a.id, b.id)
    echo(f"{a.content.lower()} {ANSI.GREY}✗ {b.content.lower()}{ANSI.RESET}")


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
        for intervention in interventions:
            ts = intervention.timestamp.strftime("%m-%d %H:%M")
            note_str = f"  ({intervention.note})" if intervention.note else ""
            echo(f"{ts}  {intervention.result:<8}  {intervention.description}{note_str}")
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
    description: str | None = None,
    done: bool = False,
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
    if focus and parent_id:
        exit_error("Error: cannot focus a subtask — set focus on the parent")
    task_id = add_task(content, focus=focus, due=resolved_due, tags=tags, parent_id=parent_id, description=description)
    if done:
        check_task(task_id)
        echo(format_status("✓", content, task_id))
        return
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


def _animate_check(label: str) -> None:
    sys.stdout.write(f"  □ {label}")
    sys.stdout.flush()
    time.sleep(0.18)
    sys.stdout.write(f"\r  {ANSI.GREEN}✓{ANSI.RESET} {ANSI.GREY}{label}{ANSI.RESET}\n")
    sys.stdout.flush()


def _animate_uncheck(label: str) -> None:
    sys.stdout.write(f"  {ANSI.GREY}✓{ANSI.RESET} {label}")
    sys.stdout.flush()
    time.sleep(0.18)
    sys.stdout.write(f"\r  □ {label}\n")
    sys.stdout.flush()


def cmd_check(args: list[str]) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life check <item>")
    task, habit = resolve_item_any(ref)
    if habit:
        updated = toggle_check(habit.id)
        if updated:
            checked_today = any(c.date() == today() for c in updated.checks)
            if checked_today:
                _animate_check(habit.content.lower())
    elif task:
        if task.completed_at:
            exit_error(f"'{task.content}' is already done")
        _, parent_completed = check_task(task.id)
        _animate_check(task.content.lower())
        if parent_completed:
            _animate_check(parent_completed.content.lower())


def cmd_uncheck(args: list[str]) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life uncheck <item>")
    task, habit = resolve_item_any(ref)
    if habit:
        today_date = today()
        checks = get_checks(habit.id)
        checked_today = any(c.date() == today_date for c in checks)
        if not checked_today:
            exit_error(f"'{habit.content}' is not checked today")
        updated = toggle_check(habit.id)
        if updated:
            checked_today = any(c.date() == today() for c in updated.checks)
            if not checked_today:
                _animate_uncheck(habit.content.lower())
    elif task:
        if not task.completed_at:
            exit_error(f"'{task.content}' is not done")
        uncheck_task(task.id)
        _animate_uncheck(task.content.lower())


def cmd_done(args: list[str]) -> None:
    cmd_check(args)


def cmd_rm(args: list[str]) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life rm <item>")
    task, habit = resolve_item_any(ref)
    if task:
        delete_task(task.id)
        echo(f"{ANSI.DIM}{task.content}{ANSI.RESET}")
    elif habit:
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


def cmd_unfocus(args: list[str]) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life unfocus <item>")
    task = resolve_task(ref)
    if not task.focus:
        exit_error(f"'{task.content}' is not focused")
    toggle_focus(task.id)
    echo(format_status("□", task.content, task.id))


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
        echo(
            format_status(
                f"{ANSI.GREY}{date_str.split('-')[2]}d:{ANSI.RESET}", task.content, task.id
            )
        )
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
    if not item:
        exit_error("Error: Item not found.")
    if item.content == to_content:
        exit_error(f"Error: Cannot rename '{item.content}' to itself.")
    if isinstance(item, Task):
        update_task(item.id, content=to_content)
    else:
        update_habit(item.id, content=to_content)
    echo(f"→ {to_content}")


def cmd_untag(tag_name: str | None, args: list[str] | None, tag_opt: str | None = None) -> None:
    cmd_tag(tag_name, args, tag_opt=tag_opt, remove=True)


def cmd_tag(
    tag_name: str | None,
    args: list[str] | None,
    tag_opt: str | None = None,
    remove: bool = False,
) -> None:
    positionals = (args or [])
    if tag_opt:
        tag_name_final = tag_opt
        item_ref = " ".join(positionals)
    else:
        if not positionals or len(positionals) < 2:
            exit_error(
                'Usage: life tag "ITEM" TAG  or  life tag "ITEM" --tag TAG'
            )
        tag_name_final = positionals[-1]
        item_ref = " ".join(positionals[:-1])
    task, habit = resolve_item_exact(item_ref)
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


def cmd_archive(args: list[str], show_list: bool = False) -> None:
    if show_list:
        habits = get_archived_habits()
        if not habits:
            echo("no archived habits")
            return
        for habit in habits:
            archived = habit.archived_at.strftime("%Y-%m-%d") if habit.archived_at else "?"
            echo(f"{ANSI.DIM}{habit.content}{ANSI.RESET}  archived {archived}")
        return
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life archive <habit>")
    habit = resolve_habit(ref)
    archive_habit(habit.id)
    echo(f"{ANSI.DIM}{habit.content}{ANSI.RESET}  archived")


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
            for date_item in dates_list:
                echo(f"{date_item.get('emoji', '📌')} {date_item['name']} - {date_item['date']}")
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
    all_tasks = get_all_tasks()
    habits = get_habits()
    today_date = today()

    untagged = [t for t in tasks if not t.tags and not t.parent_id]
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
    lines.extend(f"  ! {t.content}" for t in overdue[:3])
    lines.extend(f"  ♥ {t.content}" for t in jaynice[:3])

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
    result = backup_life()
    path = result["path"]
    rows = result["rows"]
    delta_total = result["delta_total"]
    delta_by_table = result["delta_by_table"]

    delta_str = ""
    if delta_total is not None and delta_total != 0:
        delta_str = f" (+{delta_total})" if delta_total > 0 else f" ({delta_total})"

    echo(str(path))
    echo(f"  {rows} rows{delta_str}")

    for table, delta in sorted(delta_by_table.items(), key=lambda x: abs(x[1]), reverse=True):
        sign = "+" if delta > 0 else ""
        echo(f"    {table} {sign}{delta}")


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


def cmd_defer(args: list[str], reason: str | None) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life defer <task> --reason <why>")
    if not reason:
        exit_error("--reason required. Why are you deferring this?")
    task = resolve_task(ref)
    defer_task(task.id, reason)
    echo(f"→ {task.content.lower()} deferred: {reason}")


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


def cmd_migrate() -> None:
    from . import db
    db.migrate()
    echo("migrations applied")
