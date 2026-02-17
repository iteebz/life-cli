from datetime import timedelta

import typer

from . import db
from .config import (
    get_profile,
    set_profile,
)
from .dashboard import get_pending_items, get_today_breakdown, get_today_completed
from .habits import (
    add_habit,
    delete_habit,
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
from .lib.fuzzy import find_habit, find_item, find_task, find_task_any
from .lib.parsing import parse_due_and_item, validate_content
from .lib.render import render_dashboard, render_habit_matrix, render_momentum
from .models import Habit, Task
from .momentum import weekly_momentum
from .tags import add_tag, remove_tag
from .tasks import add_task, delete_task, get_tasks, toggle_completed, toggle_focus, update_task

app = typer.Typer(
    name="life",
    help="Life CLI: manage your tasks, habits, and focus.",
    no_args_is_help=False,
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _require_task(partial: str) -> Task:
    task = find_task(partial)
    if not task:
        exit_error(f"No task found matching '{partial}'")
    return task


def _require_item(partial: str) -> tuple[Task | None, Habit | None]:
    task, habit = find_item(partial)
    if not task and not habit:
        task = find_task_any(partial)
        habit = find_habit(partial) if not task else None
    if not task and not habit:
        exit_error(f"No item found matching '{partial}'")
    return task, habit


@app.callback(invoke_without_command=True)
def dashboard(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show IDs"),  # noqa: B008
):
    """Life dashboard"""
    if ctx.invoked_subcommand is None:
        items = get_pending_items() + get_habits()
        today_items = get_today_completed()
        today_breakdown = get_today_breakdown()
        echo(render_dashboard(items, today_breakdown, None, None, today_items, verbose=verbose))


@app.command()
def task(
    content_args: list[str] = typer.Argument(..., help="Task content"),  # noqa: B008
    focus: bool = typer.Option(False, "--focus", "-f", help="Set task as focused"),  # noqa: B008
    due: str = typer.Option(
        None, "--due", "-d", help="Set due date (today, tomorrow, mon, YYYY-MM-DD)"
    ),  # noqa: B008
    tags: list[str] = typer.Option(None, "--tag", "-t", help="Add tags to task"),  # noqa: B008
    under: str = typer.Option(None, "--under", "-u", help="Parent task (fuzzy match)"),  # noqa: B008
):
    """Add task (supports focus, due date, tags, immediate completion)"""
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


@app.command()
def habit(
    content_args: list[str] = typer.Argument(..., help="Habit content"),  # noqa: B008
    tags: list[str] = typer.Option(None, "--tag", "-t", help="Add tags to habit"),  # noqa: B008
):
    """Add daily habit (auto-resets on completion)"""
    content = " ".join(content_args) if content_args else ""
    try:
        validate_content(content)
    except ValueError as e:
        exit_error(f"Error: {e}")
    habit_id = add_habit(content, tags=tags)
    echo(format_status("□", content, habit_id))


@app.command()
def done(
    args: list[str] = typer.Argument(..., help="Partial match for the item to mark done/undone"),  # noqa: B008
):
    """Mark task/habit as done or undone."""
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


@app.command()
def rm(
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),  # noqa: B008
):
    """Delete item or completed task (fuzzy match)"""
    partial = " ".join(args) if args else ""
    if not partial:
        exit_error("Usage: life rm <item>")
    task, habit = find_item(partial)
    if task:
        delete_task(task.id)
        echo(f"{ANSI.DIM}{task.content}{ANSI.RESET}")
    elif habit:
        delete_habit(habit.id)
        echo(f"{ANSI.DIM}{habit.content}{ANSI.RESET}")
    else:
        exit_error(f"No match for: {partial}")


@app.command()
def focus(
    args: list[str] = typer.Argument(..., help="Item content for fuzzy matching"),  # noqa: B008
):
    """Toggle focus status on task (fuzzy match)"""
    partial = " ".join(args) if args else ""
    if not partial:
        exit_error("Usage: life focus <item>")
    task = _require_task(partial)
    toggle_focus(task.id)
    symbol = f"{ANSI.BOLD}⦿{ANSI.RESET}" if not task.focus else "□"
    echo(format_status(symbol, task.content))


@app.command()
def due(
    args: list[str] = typer.Argument(..., help="Due date (YYYY-MM-DD) and item content"),  # noqa: B008
    remove: bool = typer.Option(False, "-r", "--remove", help="Remove due date"),  # noqa: B008
):
    """Set or remove due date on item (fuzzy match)"""
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


@app.command()
def rename(
    from_args: list[str] = typer.Argument(  # noqa: B008
        ..., help="Content to fuzzy match for the item to rename"
    ),
    to_content: str = typer.Argument(..., help="The exact new content for the item"),  # noqa: B008
):
    """Rename an item using fuzzy matching for 'from' and exact match for 'to'"""
    if not to_content:
        exit_error("Error: 'to' content cannot be empty.")
    partial_from = " ".join(from_args) if from_args else ""
    task, habit = find_item(partial_from)
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


@app.command()
def tag(
    tag_name: str | None = typer.Argument(None, help="Tag name"),  # noqa: B008
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),  # noqa: B008
    tag_opt: str | None = typer.Option(None, "--tag", "-t", help="Tag name (option form)"),  # noqa: B008
    remove: bool = typer.Option(False, "--remove", "-r", help="Remove tag instead of adding"),  # noqa: B008
):
    """Add or remove tag on item (fuzzy match)"""
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
    task, habit = find_item(item_partial)
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


@app.command()
def habits():
    """Show all habits and their checked off list for the last 7 days."""
    echo(render_habit_matrix(get_habits()))


@app.command()
def profile(
    profile_text: str = typer.Argument(None, help="Profile to set"),  # noqa: B008
):
    """View or set personal profile"""
    if profile_text:
        set_profile(profile_text)
        echo(f"Profile set to: {profile_text}")
    else:
        echo(get_profile() or "No profile set")


@app.command()
def dates(
    action: str = typer.Argument(None, help="add, remove, or list"),  # noqa: B008
    name: str = typer.Argument(None, help="Date name"),  # noqa: B008
    date_str: str = typer.Argument(None, help="Target date (YYYY-MM-DD)"),  # noqa: B008
    emoji: str = typer.Option("📌", "-e", "--emoji", help="Emoji for date"),  # noqa: B008
):
    """Add, remove, or list dates to track"""
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


@app.command()
def status():
    """Health check — untagged tasks, overdue, habit streaks, jaynice signal"""
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


@app.command()
def backup():
    """Create database backup"""
    echo(str(backup_life()))


@app.command()
def momentum():
    """Show momentum and weekly trends"""
    echo(render_momentum(weekly_momentum()))


def _set_due_relative(args: list[str], offset_days: int, label: str) -> None:
    partial = " ".join(args) if args else ""
    if not partial:
        exit_error(f"Usage: life {label} <task>")
    task = _require_task(partial)
    due_str = (today() + timedelta(days=offset_days)).isoformat()
    update_task(task.id, due=due_str)
    echo(format_status("□", task.content))


@app.command(name="today")
def today_cmd(
    args: list[str] = typer.Argument(None, help="Partial task name to set due today"),  # noqa: B008
):
    """Set due date to today on a task (fuzzy match)"""
    _set_due_relative(args, 0, "today")


@app.command()
def tomorrow(
    args: list[str] = typer.Argument(None, help="Partial task name to set due tomorrow"),  # noqa: B008
):
    """Set due date to tomorrow on a task (fuzzy match)"""
    _set_due_relative(args, 1, "tomorrow")


def main():
    db.init()
    app()


if __name__ == "__main__":
    main()
