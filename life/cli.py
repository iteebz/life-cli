import typer

from . import db
from .api import backup as backup_db
from .api import weekly_momentum
from .api.dashboard import get_pending_items, get_today_breakdown, get_today_completed
from .api.habits import (
    add_habit,
    delete_habit,
    get_all_habits,
    get_checks,
    get_habit,
    toggle_check,
    update_habit,
)
from .api.models import Task
from .api.personas import get_default_persona_name, manage_personas
from .api.tags import add_tag, get_habits_by_tag, get_tasks_by_tag, remove_tag
from .api.tasks import add_task, complete_task, delete_task, get_all_tasks, update_task
from .config import (
    add_countdown,
    get_context,
    get_countdowns,
    get_profile,
    set_context,
    set_profile,
)
from .lib.ansi import ANSI
from .lib.claude import invoke
from .lib.clock import today
from .lib.fuzzy import find_habit, find_task
from .lib.render import render_dashboard, render_habit_matrix, render_item_list

app = typer.Typer(
    name="life",
    help="Life CLI: manage your tasks, habits, and focus.",
    no_args_is_help=False,
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def _dashboard(ctx: typer.Context):
    """Ephemeral life agent"""
    if ctx.invoked_subcommand is None:
        items = get_pending_items()
        life_context = get_context()
        life_profile = get_profile()
        today_items = get_today_completed()
        today_breakdown = get_today_breakdown()
        momentum = weekly_momentum()
        typer.echo(
            render_dashboard(
                items, today_breakdown, momentum, life_context, today_items, life_profile
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
    task_id = add_task(content, focus=focus, due=due, tags=tags)
    typer.echo(f"Added task: {content} {ANSI.GREY}{task_id}{ANSI.RESET}")


@app.command()
def habit(
    content: str = typer.Argument(..., help="Habit content"),  # noqa: B008
    tags: list[str] = typer.Option(None, "--tag", "-t", help="Add tags to habit"),  # noqa: B008
):
    """Add daily habit (auto-resets on completion)"""
    habit_id = add_habit(content, tags=tags)
    typer.echo(f"Added habit: {content} {ANSI.GREY}{habit_id}{ANSI.RESET}")


@app.command()
def done(
    partial: str = typer.Argument(..., help="Partial match for the item to mark done/undone"),
):
    """Mark an item as complete/checked or uncomplete/unchecked."""
    task = find_task(partial)
    habit = find_habit(partial) if not task else None

    if not task and not habit:
        typer.echo(f"{ANSI.RED}Error:{ANSI.RESET} No item found matching '{partial}'")
        raise typer.Exit(code=1)

    is_habit = habit is not None
    if is_habit:
        today_date = today()
        checks = get_checks(habit.id)
        is_undo_action = today_date in checks
        toggle_check(habit.id)
        if is_undo_action:
            typer.echo(f"{ANSI.YELLOW}Habit:{ANSI.RESET} '{habit.content}' unchecked.")
        else:
            typer.echo(f"{ANSI.GREEN}Habit:{ANSI.RESET} '{habit.content}' checked for today.")
    else:
        if task.completed is not None:
            update_task(task.id, completed=None)
            typer.echo(f"Task: '{task.content}' marked as pending.")
        else:
            complete_task(task.id)
            typer.echo(f"Task: '{task.content}' marked as complete.")


@app.command()
def rm(
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),  # noqa: B008
):
    """Delete item or completed task (fuzzy match)"""
    if not args:
        typer.echo("Usage: life rm <item>")
        raise typer.Exit(1)
    partial = " ".join(args)
    task = find_task(partial)
    if task:
        delete_task(task.id)
        typer.echo(f"Removed: {task.content}")
    else:
        habit = find_habit(partial)
        if habit:
            delete_habit(habit.id)
            typer.echo(f"Removed: {habit.content}")
        else:
            typer.echo(f"No match for: {partial}")


def _parse_due_date(date_str: str) -> str | None:
    """Parse due date string into YYYY-MM-DD format."""
    from datetime import datetime, timedelta

    date_str_lower = date_str.lower()

    if date_str_lower == "today":
        return today().isoformat()
    if date_str_lower == "tomorrow":
        return (today() + timedelta(days=1)).isoformat()

    days_of_week = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
    if date_str_lower in days_of_week:
        target_day = days_of_week[date_str_lower]
        current_day = today().weekday()
        days_ahead = target_day - current_day
        if days_ahead <= 0:
            days_ahead += 7
        return (today() + timedelta(days=days_ahead)).isoformat()

    try:
        datetime.fromisoformat(date_str)
        return date_str
    except ValueError:
        return None


@app.command()
def focus(
    args: list[str] = typer.Argument(  # noqa: B008
        None, help="Item content for fuzzy matching or 'list' to show focus items"
    ),
):
    """Toggle focus status on item (fuzzy match) or list focus items"""
    if not args:
        typer.echo(
            "No arguments provided. Use 'list' to show focus items or provide an item to toggle focus."
        )
        return

    first_arg = args[0].lower()
    valid_personas = {"roast", "pepper", "kim"}

    if first_arg in valid_personas and len(args) > 1:
        pass
        # focus_items = get_focus_items()
        # focus_list = render_focus_items(focus_items)
        # message = f"{' '.join(args[1:])} Here are my focus items:\n{focus_list}"


@app.command()
def due(
    args: list[str] = typer.Argument(..., help="Due date (YYYY-MM-DD) and item content"),  # noqa: B008
    remove: bool = typer.Option(False, "-r", "--remove", help="Remove due date"),  # noqa: B008
):
    """Set or remove due date on item (fuzzy match)"""
    if not args:
        typer.echo("Due date and item required")
        raise typer.Exit(1)

    date_str = None
    item_args = args

    if not remove and len(args) > 0:
        parsed = _parse_due_date(args[0])
        if parsed:
            date_str = parsed
            item_args = args[1:]

    if not item_args:
        typer.echo("Item name required")
        raise typer.Exit(1)

    partial = " ".join(item_args)
    task = find_task(partial)
    if not task:
        typer.echo(f"No match for: {partial}")
        raise typer.Exit(1)

    if remove:
        update_task(task.id, due=None)
        typer.echo(f"Due date removed: {task.content}")
    elif date_str:
        update_task(task.id, due=date_str)
        typer.echo(f"Due: {task.content} on {date_str}")
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

    partial_from = " ".join(from_args)
    task = find_task(partial_from)
    item_to_rename = task if task else find_habit(partial_from)

    if not item_to_rename:
        typer.echo(f"No fuzzy match found for: '{partial_from}'")
        raise typer.Exit(code=1)

    if item_to_rename.content == to_content:
        typer.echo(f"Error: Cannot rename '{item_to_rename.content}' to itself.")
        raise typer.Exit(code=1)

    if isinstance(item_to_rename, Task):
        update_task(item_to_rename.id, content=to_content)
    else:
        update_habit(item_to_rename.id, content=to_content)
    typer.echo(f"Updated: '{item_to_rename.content}' → '{to_content}'")


@app.command()
def tag(
    tag_name: str = typer.Argument(..., help="Tag name"),  # noqa: B008
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),  # noqa: B008
    remove: bool = typer.Option(False, "--remove", "-r", help="Remove tag instead of adding"),  # noqa: B008
    completed: bool = typer.Option(
        False, "--completed", "-c", help="Include completed items in search"
    ),  # noqa: B008
):
    """Add, remove, or view items by tag (fuzzy match)"""
    item_partial = " ".join(args) if args else None

    if item_partial:
        task = find_task(item_partial)
        habit = find_habit(item_partial) if not task else None

        if task:
            if remove:
                remove_tag(task.id, None, tag_name)
                typer.echo(f"Untagged: {task.content} ← {ANSI.GREY}#{tag_name}{ANSI.RESET}")
            else:
                add_tag(task.id, None, tag_name)
                typer.echo(f"Tagged: {task.content} {ANSI.GREY}#{tag_name}{ANSI.RESET}")
        elif habit:
            if remove:
                remove_tag(None, habit.id, tag_name)
                typer.echo(f"Untagged: {habit.content} ← {ANSI.GREY}#{tag_name}{ANSI.RESET}")
            else:
                add_tag(None, habit.id, tag_name)
                typer.echo(f"Tagged: {habit.content} {ANSI.GREY}#{tag_name}{ANSI.RESET}")
        else:
            typer.echo(f"No match for: {item_partial}")
    else:
        tasks = get_tasks_by_tag(tag_name)
        habits = get_habits_by_tag(tag_name)
        items = tasks + habits
        if items:
            typer.echo(f"\n{tag_name.upper()} ({len(items)}):")
            typer.echo(render_item_list(items))
        else:
            typer.echo(f"No items tagged with #{tag_name}")


@app.command()
def check(
    item_id: str = typer.Argument(..., help="The ID of the habit to check"),  # noqa: B008
):
    """Mark a habit as checked for today."""
    try:
        toggle_check(item_id)
        habit = get_habit(item_id)
        if habit:
            typer.echo(f"Checked: {habit.content}")
        else:
            typer.echo(f"Error: Habit with ID {item_id} not found after checking.")
            raise typer.Exit(code=1)
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1) from e


@app.command()
def habits():
    """Show all habits and their checked off list for the last 7 days."""
    typer.echo(render_habit_matrix())


@app.command()
def profile(
    profile_text: str = typer.Argument(None, help="Profile to set"),  # noqa: B008
):
    """View or set personal profile"""
    if profile_text:
        set_profile(profile_text)
        typer.echo(f"Profile set to: {profile_text}")
    else:
        current = get_profile()
        typer.echo(current if current else "No profile set")


@app.command()
def context(
    context_text: str = typer.Argument(None, help="Context text to set"),  # noqa: B008
):
    """View or set current context"""
    if context_text:
        set_context(context_text)
        typer.echo(f"Context set to: {context_text}")
    else:
        typer.echo(get_context())


@app.command()
def countdown(
    action: str = typer.Argument(None, help="add, remove, or list"),  # noqa: B008
    name: str = typer.Argument(None, help="Countdown name"),  # noqa: B008
    date_str: str = typer.Argument(None, help="Target date (YYYY-MM-DD)"),  # noqa: B008
    emoji: str = typer.Option("📌", "-e", "--emoji", help="Emoji for countdown"),  # noqa: B008
):
    """Add, remove, or list countdowns to target dates"""
    if not action:
        countdowns = get_countdowns()
        if countdowns:
            for cd in sorted(countdowns, key=lambda x: x["date"]):
                typer.echo(f"{cd.get('emoji', '📌')} {cd['name']} - {cd['date']}")
        else:
            typer.echo("No countdowns set")
        return

    if action == "add":
        if not name or not date_str:
            typer.echo("Error: add requires name and date (YYYY-MM-DD)", err=True)
            raise typer.Exit(1)
        add_countdown(name, date_str, emoji)
        typer.echo(f"Added countdown: {emoji} {name} on {date_str}")
    elif action == "remove":
        if not name:
            typer.echo("Error: remove requires a countdown name", err=True)
            raise typer.Exit(1)
        from .config import remove_countdown

        remove_countdown(name)
        typer.echo(f"Removed countdown: {name}")
    else:
        typer.echo(
            f"Error: unknown action '{action}'. Use 'add', 'remove', or no argument to list.",
            err=True,
        )
        raise typer.Exit(1)


@app.command()
def backup():
    """Create database backup"""
    typer.echo(backup_db())


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
def roast(
    message: str = typer.Argument(..., help="The message to send to the Roast persona."),
):
    """Invoke the Roast persona."""
    invoke(message, "roast")


@app.command()
def pepper(
    message: str = typer.Argument(..., help="The message to send to the Pepper persona."),
):
    """Invoke the Pepper persona."""
    invoke(message, "pepper")


@app.command()
def kim(
    message: str = typer.Argument(..., help="The message to send to the Kim persona."),
):
    """Invoke the Kim persona."""
    invoke(message, "kim")


@app.command()
def chat(
    args: list[str] = typer.Argument(None, help="Message to send to agent"),  # noqa: B008
    persona: str = typer.Option(None, help="Persona to use (roast, pepper, kim)"),  # noqa: B008
):
    """Chat with ephemeral agent."""
    message = " ".join(args) if args else ""
    if not message:
        typer.echo("Error: message required")
        raise typer.Exit(1)
    default_persona = "roast"
    selected_persona = persona or get_default_persona_name() or default_persona
    invoke(message, selected_persona)


@app.command(name="items")
def list_items():
    """List all items."""

    tasks = get_all_tasks()
    habits = get_all_habits()
    items = tasks + habits
    typer.echo(render_item_list(items))


@app.command(name="dashboard")
def show_dashboard():
    """Show dashboard summary."""
    typer.echo(render_dashboard())


def main():
    """Check for personas before passing to typer."""
    db.init()
    app()


if __name__ == "__main__":
    main()
