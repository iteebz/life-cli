import typer

from . import db
from .api import backup as backup_db
from .api import get_item, weekly_momentum
from .api.checks import add_check, get_checks
from .api.items import add_item, get_all_items, update_item
from .config import (
    add_countdown,
    get_context,
    get_countdowns,
    get_profile,
    set_context,
    set_profile,
)
from .lib.ansi import ANSI
from .lib.claude import invoke as invoke_claude
from .lib.clock import today
from .lib.render import render_dashboard, render_habit_matrix, render_item_list
from .ops.dashboard import get_pending_items, get_today_breakdown, get_today_completed
from .ops.fuzzy import find_item
from .ops.items import manage_tag, set_due
from .ops.items import remove as remove_item
from .ops.personas import get_default_persona_name, manage_personas
from .ops.toggle import toggle_done

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
    item_id = add_item(content, item_type="task", is_repeat=False, focus=focus, due=due, tags=tags)
    typer.echo(f"Added task: {content} {ANSI.GREY}{item_id}{ANSI.RESET}")


@app.command()
def habit(
    content: str = typer.Argument(..., help="Habit content"),  # noqa: B008
    focus: bool = typer.Option(False, "--focus", "-f", help="Set habit as focused"),  # noqa: B008
    tags: list[str] = typer.Option(None, "--tag", "-t", help="Add tags to habit"),  # noqa: B008
):
    """Add daily habit (auto-resets on completion)"""
    item_id = add_item(content, item_type="habit", is_repeat=True, focus=focus, due=None, tags=tags)
    typer.echo(f"Added habit: {content} {ANSI.GREY}{item_id}{ANSI.RESET}")


@app.command()
def chore(
    content: str = typer.Argument(..., help="Chore content"),  # noqa: B008
    focus: bool = typer.Option(False, "--focus", "-f", help="Set chore as focused"),  # noqa: B008
    tags: list[str] = typer.Option(None, "--tag", "-t", help="Add tags to chore"),  # noqa: B008
):
    """Add daily chore (auto-resets on completion)"""
    item_id = add_item(content, item_type="chore", is_repeat=True, focus=focus, due=None, tags=tags)
    typer.echo(f"Added chore: {content} {ANSI.GREY}{item_id}{ANSI.RESET}")


@app.command()
def done(
    partial: str = typer.Argument(..., help="Partial match for the item to mark done/undone"),
):
    """Mark an item as complete/checked or uncomplete/unchecked."""
    item = find_item(partial)

    if not item:
        typer.echo(f"{ANSI.RED}Error:{ANSI.RESET} No item found matching '{partial}'")
        raise typer.Exit(code=1)

    if item.is_habit:
        today_str = today().isoformat()
        checks = get_checks(item.id)
        is_undo_action = today_str in checks
    else:
        is_undo_action = item.completed is not None

    result = toggle_done(partial, undo=is_undo_action)

    if result:
        content, status = result
        if item.is_habit:
            if status == "done":
                typer.echo(f"{ANSI.GREEN}Habit:{ANSI.RESET} '{content}' checked for today.")
            else:
                typer.echo(f"{ANSI.YELLOW}Habit:{ANSI.RESET} '{content}' unchecked.")
        else:
            if status == "done":
                typer.echo(f"Task: '{content}' marked as complete.")
            else:
                typer.echo(f"Task: '{content}' marked as pending.")


@app.command()
def rm(
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),  # noqa: B008
):
    """Delete item or completed task (fuzzy match)"""
    if not args:
        typer.echo("Usage: life rm <item>")
        raise typer.Exit(1)
    partial = " ".join(args)
    result = remove_item(partial)
    typer.echo(f"Removed: {result}" if result else f"No match for: {partial}")


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
    typer.echo(set_due(list(args) if args else [], remove=remove))


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
    item_to_rename = find_item(partial_from)

    if not item_to_rename:
        typer.echo(f"No fuzzy match found for: '{partial_from}'")
        raise typer.Exit(code=1)

    if item_to_rename.content == to_content:
        typer.echo(f"Error: Cannot rename '{item_to_rename.content}' to itself.")
        raise typer.Exit(code=1)

    update_item(item_to_rename.id, content=to_content)
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
    typer.echo(
        manage_tag(
            tag_name, " ".join(args) if args else None, remove=remove, include_completed=completed
        )
    )


@app.command()
def check(
    item_id: str = typer.Argument(..., help="The ID of the item to check"),  # noqa: B008
):
    """Mark a habit or chore as checked for today."""
    try:
        add_check(item_id)
        item = get_item(item_id)
        if item:
            typer.echo(f"Checked: {item.content}")
        else:
            typer.echo(f"Error: Item with ID {item_id} not found after checking.")
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
    invoke_claude(message, "roast")


@app.command()
def pepper(
    message: str = typer.Argument(..., help="The message to send to the Pepper persona."),
):
    """Invoke the Pepper persona."""
    invoke_claude(message, "pepper")


@app.command()
def kim(
    message: str = typer.Argument(..., help="The message to send to the Kim persona."),
):
    """Invoke the Kim persona."""
    invoke_claude(message, "kim")


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
    invoke_claude(message, selected_persona)


@app.command(name="items")
def list_items():
    """List all items."""
    items = get_all_items()
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
