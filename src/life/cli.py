import sys

import typer

from .claude import invoke as invoke_claude
from .config import get_default_persona, backup, get_or_set_profile, get_or_set_context, manage_personas
from .display import render_dashboard
from .tags import manage_tag
from .tasks import add_task, add_habit, add_chore, done_item, get_pending_items, today_completed, weekly_momentum, get_today_completed
from .utils import delete_item_msg, toggle_focus_msg, set_due, edit_item
from .config import get_context

app = typer.Typer()

KNOWN_COMMANDS = {
    "add", "task", "habit", "chore", "done", "rm", "delete", "focus",
    "due", "edit", "tag", "profile", "context", "backup", "personas",
    "help", "--help", "-h",
}


def _is_message(raw_args: list[str]) -> bool:
    """Check if args represent a chat message (not a command)."""
    if not raw_args:
        return False
    first_arg = raw_args[0].lower()
    return first_arg not in KNOWN_COMMANDS and not first_arg.startswith("-")


def _maybe_spawn_persona() -> bool:
    """Check if we should spawn persona. Returns True if spawned."""
    raw_args = sys.argv[1:]

    if not raw_args or raw_args[0] in ("--help", "-h", "--show-completion", "--install-completion"):
        return False

    valid_personas = {"roast", "pepper", "kim"}

    if raw_args[0] in valid_personas:
        persona = raw_args[0]
        raw_args = raw_args[1:]
        if _is_message(raw_args):
            message = " ".join(raw_args)
            invoke_claude(message, persona)
            return True
    elif _is_message(raw_args):
        default = get_default_persona()
        if default:
            message = " ".join(raw_args)
            invoke_claude(message, default)
            return True

    return False


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Ephemeral life agent"""
    if ctx.invoked_subcommand is None:
        items = get_pending_items()
        today_count = today_completed()
        momentum = weekly_momentum()
        life_context = get_context()
        today_items = get_today_completed()
        typer.echo(render_dashboard(items, today_count, momentum, life_context, today_items))


@app.command()
def task(
    args: list[str] = typer.Argument(..., help="Task content"),  # noqa: B008
    focus: bool = typer.Option(False, "-f", "--focus", help="Mark as focus item"),  # noqa: B008
    due: str = typer.Option(None, "-d", "--due", help="Due date (YYYY-MM-DD)"),  # noqa: B008
    done: bool = typer.Option(False, "-x", "--done", help="Immediately mark item as done"),  # noqa: B008
    tag: list[str] = typer.Option(None, "-t", "--tag", help="Add tags to item"),  # noqa: B008
):
    """Add task"""
    typer.echo(add_task(" ".join(args), focus=focus, due=due, done=done, tags=tag))


app.command(name="add")(task)


@app.command()
def habit(content: str = typer.Argument(..., help="Habit content")):  # noqa: B008
    """Add habit"""
    typer.echo(add_habit(content))


@app.command()
def chore(content: str = typer.Argument(..., help="Chore content")):  # noqa: B008
    """Add chore"""
    typer.echo(add_chore(content))


@app.command()
def done(
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),  # noqa: B008
    undo: bool = typer.Option(False, "-u", "--undo", "-r", "--remove", help="Undo item completion"),  # noqa: B008
):
    """Complete or check item (fuzzy match)"""
    typer.echo(done_item(" ".join(args) if args else "", undo=undo))


@app.command(name="rm")
def delete_item(
    args: list[str] = typer.Argument(..., help="Item content for fuzzy matching"),  # noqa: B008
):
    """Remove item (fuzzy match)"""
    typer.echo(delete_item_msg(" ".join(args)))


app.command(name="delete")(delete_item)


@app.command()
def focus(
    args: list[str] = typer.Argument(..., help="Item content for fuzzy matching"),  # noqa: B008
):
    """Toggle focus on item (fuzzy match)"""
    typer.echo(toggle_focus_msg(" ".join(args)))


@app.command()
def due(
    args: list[str] = typer.Argument(..., help="Due date (YYYY-MM-DD) and item content"),  # noqa: B008
    remove: bool = typer.Option(False, "-r", "--remove", help="Remove due date"),  # noqa: B008
):
    """Set due date on item (fuzzy match)"""
    typer.echo(set_due(list(args) if args else [], remove=remove))


@app.command()
def edit(
    new_content: str = typer.Argument(..., help="New item description"),  # noqa: B008
    args: list[str] = typer.Argument(..., help="Item content for fuzzy matching"),  # noqa: B008
):
    """Edit item description (fuzzy match)"""
    typer.echo(edit_item(new_content, " ".join(args)))


@app.command()
def tag(
    tag_name: str = typer.Argument(..., help="Tag name"),  # noqa: B008
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),  # noqa: B008
    remove: bool = typer.Option(False, "--remove", "-r", help="Remove tag instead of adding"),  # noqa: B008
):
    """Add/remove tag to/from item (fuzzy match), or view items by tag"""
    typer.echo(manage_tag(tag_name, " ".join(args) if args else None, remove=remove))


@app.command()
def profile(
    profile_text: str = typer.Argument(None, help="Profile to set"),  # noqa: B008
):
    """View or update your profile"""
    typer.echo(get_or_set_profile(profile_text))


@app.command()
def context(
    context_text: str = typer.Argument(None, help="Context text to set"),  # noqa: B008
):
    """View or update your context"""
    typer.echo(get_or_set_context(context_text))


@app.command()
def personas(
    name: str = typer.Argument(None, help="Persona name (roast, pepper, kim)"),  # noqa: B008
    set: bool = typer.Option(False, "-s", "--set", help="Set as default persona"),  # noqa: B008
    prompt: bool = typer.Option(False, "-p", "--prompt", help="Show full ephemeral prompt"),  # noqa: B008
):
    """Show available personas or view/set a specific persona"""
    try:
        typer.echo(manage_personas(name, set_default=set, show_prompt=prompt))
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None  # noqa: B904


@app.command()
def backup_cmd():
    """Backup database"""
    typer.echo(backup())


def main_with_personas():
    """Wrapper that checks for personas before passing to typer."""
    if _maybe_spawn_persona():
        sys.exit(0)
    app()


if __name__ == "__main__":
    main_with_personas()
