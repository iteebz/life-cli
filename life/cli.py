from datetime import timedelta

import typer

from . import db
from .chat import invoke
from .config import (
    get_context,
    get_profile,
    set_context,
    set_profile,  # noqa: F401
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
from .lib.format import format_habit, format_status, format_task
from .lib.fuzzy import find_item, find_task, find_task_any
from .lib.parsing import parse_due_and_item, validate_content
from .lib.render import render_dashboard, render_habit_matrix, render_item_list, render_momentum
from .momentum import weekly_momentum
from .personas import get_default_persona_name, manage_personas
from .tags import add_tag, remove_tag
from .tasks import add_task, delete_task, get_tasks, toggle_completed, toggle_focus, update_task

app = typer.Typer(
    name="life",
    help="Life CLI: manage your tasks, habits, and focus.",
    no_args_is_help=False,
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback(invoke_without_command=True)
def _dashboard(ctx: typer.Context):
    """Ephemeral life agent"""
    if ctx.invoked_subcommand is None:
        items = get_pending_items() + get_habits()
        today_items = get_today_completed()
        today_breakdown = get_today_breakdown()
        typer.echo(
            render_dashboard(
                items, today_breakdown, None, None, today_items
            )
        )


@app.command()
def task(
    content: str = typer.Argument(..., help="Task content"),  # noqa: B008
    focus: bool = typer.Option(False, "--focus", "-f", help="Set task as focused"),  # noqa: B008
    due: str = typer.Option(
        None, "--due", "-d", help="Set due date (today, tomorrow, mon, YYYY-MM-DD)"
    ),  # noqa: B008
    tags: list[str] = typer.Option(None, "--tag", "-t", help="Add tags to task"),  # noqa: B008
):
    """Add task (supports focus, due date, tags, immediate completion)"""
    try:
        validate_content(content)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    resolved_due = parse_due_date(due) if due else None
    task_id = add_task(content, focus=focus, due=resolved_due, tags=tags)
    symbol = f"{ANSI.BOLD}⦿{ANSI.RESET}" if focus else "□"
    typer.echo(format_status(symbol, content, task_id))


@app.command()
def habit(
    content: str = typer.Argument(..., help="Habit content"),  # noqa: B008
    tags: list[str] = typer.Option(None, "--tag", "-t", help="Add tags to habit"),  # noqa: B008
):
    """Add daily habit (auto-resets on completion)"""
    try:
        validate_content(content)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    habit_id = add_habit(content, tags=tags)
    typer.echo(format_status("□", content, habit_id))


@app.command()
def done(
    partial: str = typer.Argument(..., help="Partial match for the item to mark done/undone"),
):
    """Mark task/habit as done or undone."""
    task, habit = find_item(partial)

    if not task and not habit:
        typer.echo(f"{ANSI.RED}Error:{ANSI.RESET} No item found matching '{partial}'")
        raise typer.Exit(code=1)

    if habit:
        today_date = today()
        checks = get_checks(habit.id)
        is_undo_action = today_date in checks
        toggle_check(habit.id)
        checked = not is_undo_action
        typer.echo(format_habit(habit, checked=checked))
    elif task:
        toggle_completed(task.id)
        typer.echo(format_task(task))


@app.command()
def rm(
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),  # noqa: B008
):
    """Delete item or completed task (fuzzy match)"""
    partial = " ".join(args) if args else ""
    if not partial:
        typer.echo("Usage: life rm <item>")
        raise typer.Exit(1)
    task, habit = find_item(partial)
    if task:
        delete_task(task.id)
        typer.echo(f"{ANSI.DIM}{task.content}{ANSI.RESET}")
    elif habit:
        delete_habit(habit.id)
        typer.echo(f"{ANSI.DIM}{habit.content}{ANSI.RESET}")
    else:
        typer.echo(f"No match for: {partial}")


@app.command()
def focus(
    args: list[str] = typer.Argument(..., help="Item content for fuzzy matching"),  # noqa: B008
):
    """Toggle focus status on task (fuzzy match)"""
    partial = " ".join(args) if args else ""
    if not partial:
        typer.echo("Usage: life focus <item>")
        raise typer.Exit(1)

    task = find_task(partial)
    if not task:
        typer.echo(f"No task found matching '{partial}'")
        raise typer.Exit(1)

    toggle_focus(task.id)
    symbol = f"{ANSI.BOLD}⦿{ANSI.RESET}" if not task.focus else "□"
    typer.echo(format_status(symbol, task.content))


@app.command()
def due(
    args: list[str] = typer.Argument(..., help="Due date (YYYY-MM-DD) and item content"),  # noqa: B008
    remove: bool = typer.Option(False, "-r", "--remove", help="Remove due date"),  # noqa: B008
):
    """Set or remove due date on item (fuzzy match)"""
    try:
        date_str, item_name = parse_due_and_item(args, remove=remove)
    except ValueError as e:
        typer.echo(str(e))
        raise typer.Exit(1) from None

    task = find_task(item_name)
    if not task:
        typer.echo(f"No match for: {item_name}")
        raise typer.Exit(1)

    if remove:
        update_task(task.id, due=None)
        typer.echo(format_status("□", task.content))
    elif date_str:
        update_task(task.id, due=date_str)
        typer.echo(
            format_status(f"{ANSI.GREY}{date_str.split('-')[2]}d:{ANSI.RESET}", task.content)
        )
    else:
        typer.echo(
            "Due date required (today, tomorrow, day name, or YYYY-MM-DD) or use -r/--remove to clear"
        )
        raise typer.Exit(1)


@app.command()
def rename(
    from_args: list[str] = typer.Argument(  # noqa: B008
        ..., help="Content to fuzzy match for the item to rename"
    ),
    to_content: str = typer.Argument(..., help="The exact new content for the item"),  # noqa: B008
):
    """Rename an item using fuzzy matching for 'from' and exact match for 'to'"""
    if not to_content:
        typer.echo("Error: 'to' content cannot be empty.")
        raise typer.Exit(code=1)

    partial_from = " ".join(from_args) if from_args else ""
    task, habit = find_item(partial_from)
    item_to_rename = task or habit

    if not item_to_rename:
        typer.echo(f"No fuzzy match found for: '{partial_from}'")
        raise typer.Exit(code=1)

    if item_to_rename.content == to_content:
        typer.echo(f"Error: Cannot rename '{item_to_rename.content}' to itself.")
        raise typer.Exit(code=1)

    if hasattr(item_to_rename, "focus"):
        update_task(item_to_rename.id, content=to_content)
    else:
        update_habit(item_to_rename.id, content=to_content)
    typer.echo(f"Updated: '{item_to_rename.content}' → '{to_content}'")


@app.command()
def tag(
    tag_name: str | None = typer.Argument(None, help="Tag name"),  # noqa: B008
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),  # noqa: B008
    tag_opt: str | None = typer.Option(None, "--tag", "-t", help="Tag name (option form)"),  # noqa: B008
    remove: bool = typer.Option(False, "--remove", "-r", help="Remove tag instead of adding"),  # noqa: B008
):
    """Add or remove tag on item (fuzzy match)"""
    # Support both syntaxes:
    # - `life tag finance home loan` (positional tag_name + item args)
    # - `life tag home loan --tag finance` (option tag + item args)
    if tag_opt:
        tag_name_final = tag_opt
        positionals = ([tag_name] if tag_name else []) + (args or [])
        item_partial = " ".join(positionals)
    else:
        if not tag_name or not args:
            typer.echo(
                "Error: Missing arguments. Use `life tag TAG ITEM...` or `life tag ITEM... --tag TAG`."
            )
            raise typer.Exit(1)
        tag_name_final = tag_name
        item_partial = " ".join(args)
    task, habit = find_item(item_partial)

    # If no pending task/habit match, allow tagging completed tasks as well.
    if not task and not habit:
        task = find_task_any(item_partial)
        if not task:
            typer.echo(f"No match for: {item_partial}")
            raise typer.Exit(1)

    if task:
        if remove:
            remove_tag(task.id, None, tag_name_final)
            typer.echo(f"Untagged: {task.content} ← {ANSI.GREY}#{tag_name_final}{ANSI.RESET}")
        else:
            add_tag(task.id, None, tag_name_final)
            typer.echo(f"Tagged: {task.content} {ANSI.GREY}#{tag_name_final}{ANSI.RESET}")
    elif habit:
        if remove:
            remove_tag(None, habit.id, tag_name_final)
            typer.echo(f"Untagged: {habit.content} ← {ANSI.GREY}#{tag_name_final}{ANSI.RESET}")
        else:
            add_tag(None, habit.id, tag_name_final)
            typer.echo(f"Tagged: {habit.content} {ANSI.GREY}#{tag_name_final}{ANSI.RESET}")


@app.command()
def habits():
    """Show all habits and their checked off list for the last 7 days."""
    typer.echo(render_habit_matrix(get_habits()))


@app.command()
def profile(
    profile_text: str = typer.Argument(..., help="Profile to set"),  # noqa: B008
):
    """Set personal profile"""
    set_profile(profile_text)
    typer.echo(f"Profile set to: {profile_text}")


@app.command()
def context(
    context_text: str = typer.Argument(..., help="Context text to set"),  # noqa: B008
):
    """Set current context"""
    set_context(context_text)
    typer.echo(f"Context set to: {context_text}")


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
                typer.echo(f"{d.get('emoji', '📌')} {d['name']} - {d['date']}")
        else:
            typer.echo("No dates set")
        return

    if action == "add":
        if not name or not date_str:
            typer.echo("Error: add requires name and date (YYYY-MM-DD)", err=True)
            raise typer.Exit(1)
        add_date(name, date_str, emoji)
        typer.echo(f"Added date: {emoji} {name} on {date_str}")
    elif action == "remove":
        if not name:
            typer.echo("Error: remove requires a date name", err=True)
            raise typer.Exit(1)
        remove_date(name)
        typer.echo(f"Removed date: {name}")
    else:
        typer.echo(
            f"Error: unknown action '{action}'. Use 'add', 'remove', or no argument to list.",
            err=True,
        )
        raise typer.Exit(1)


@app.command()
def backup():
    """Create database backup"""
    typer.echo(backup_life())


@app.command()
def personas(
    name: str = typer.Argument(None, help="Persona name (roast, pepper, kim)"),  # noqa: B008
    set: bool = typer.Option(False, "-s", "--set", help="Set as default persona"),  # noqa: B008
    prompt: bool = typer.Option(False, "-p", "--prompt", help="Show full ephemeral prompt"),  # noqa: B008
):
    """View or set AI personas (roast, pepper, kim)"""
    try:
        typer.echo(manage_personas(name, set_default=set, show_prompt=prompt))
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None  # noqa: B904


@app.command()
def chat(
    args: list[str] = typer.Argument(None, help="Message to send to agent"),  # noqa: B008
):
    """Chat with ephemeral agent."""
    message = " ".join(args) if args else ""
    if not message:
        typer.echo("Error: message required")
        raise typer.Exit(1)
    default_persona = "roast"
    selected_persona = get_default_persona_name() or default_persona
    invoke(message, selected_persona)


@app.command(name="list")
def list_items():
    """List all items."""

    tasks = get_tasks()
    habits = get_habits()
    items = tasks + habits
    typer.echo(render_item_list(items))


@app.command()
def momentum():
    """Show momentum and weekly trends"""
    typer.echo(render_momentum(weekly_momentum()))


@app.command(name="today")
def today_cmd(
    args: list[str] = typer.Argument(None, help="Partial task name to set due today"),  # noqa: B008
):
    """Set due date to today on a task (fuzzy match)"""
    partial = " ".join(args) if args else ""
    if not partial:
        typer.echo("Usage: life today <task>")
        raise typer.Exit(1)
    task = find_task(partial)
    if not task:
        typer.echo(f"No task found matching '{partial}'")
        raise typer.Exit(1)
    due_str = today().isoformat()
    update_task(task.id, due=due_str)
    typer.echo(format_status("□", task.content))


@app.command()
def tomorrow(
    args: list[str] = typer.Argument(None, help="Partial task name to set due tomorrow"),  # noqa: B008
):
    """Set due date to tomorrow on a task (fuzzy match)"""
    partial = " ".join(args) if args else ""
    if not partial:
        typer.echo("Usage: life tomorrow <task>")
        raise typer.Exit(1)
    task = find_task(partial)
    if not task:
        typer.echo(f"No task found matching '{partial}'")
        raise typer.Exit(1)
    due_str = (today() + timedelta(days=1)).isoformat()
    update_task(task.id, due=due_str)
    typer.echo(format_status("□", task.content))


def main():
    """Check for personas before passing to typer."""
    db.init()
    app()


if __name__ == "__main__":
    main()
