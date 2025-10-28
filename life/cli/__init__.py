import typer

from .. import db
from ..api import weekly_momentum
from ..config import get_context, get_profile
from ..lib.render import render_dashboard
from ..ops.dashboard import get_pending_items, get_today_breakdown, get_today_completed

# Import cmd objects from submodules
from .backup import cmd as backup_cmd
from .chat import cmd as chat_cmd
from .check import cmd as check_cmd
from .chore import cmd as chore_cmd  # New import
from .context import cmd as context_cmd
from .countdown import cmd as countdown_cmd
from .done import done as done_command  # Assuming done.py will be created
from .due import cmd as due_cmd
from .focus import cmd as focus_cmd
from .habit import cmd as habit_cmd
from .habits import cmd as habits_cmd
from .items import cmd as items_cmd  # Added this import
from .kim import cmd as kim_cmd
from .pepper import cmd as pepper_cmd
from .personas import cmd as personas_cmd
from .profile import cmd as profile_cmd
from .rename import cmd as rename_cmd
from .rm import cmd as rm_cmd
from .roast import cmd as roast_cmd
from .tag import cmd as tag_cmd
from .task import task  # Import the task function directly

app = typer.Typer(
    name="life",
    help="Life CLI: manage your tasks, habits, and focus.",
    no_args_is_help=False,  # Changed from True
    add_completion=False,  # Consolidated add_completion here
)

# Register all commands directly
app.command(name="task", help="Add task (supports focus, due date, tags, immediate completion)")(
    task
)
app.add_typer(habit_cmd, name="habit", help="Add daily habit (auto-resets on completion)")
app.add_typer(
    chore_cmd, name="chore", help="Add daily chore (auto-resets on completion)"
)  # New registration
app.command(name="done", help="Mark item complete or undo completion (fuzzy match)")(
    done_command
)  # Assuming done.py will be created
app.add_typer(rm_cmd, name="rm", help="Delete item or completed task (fuzzy match)")
app.add_typer(focus_cmd, name="focus", help="Toggle focus status on item (fuzzy match)")
app.add_typer(due_cmd, name="due", help="Set or remove due date on item (fuzzy match)")
app.add_typer(rename_cmd, name="rename", help="Change item description (fuzzy match)")
app.add_typer(tag_cmd, name="tag", help="Add, remove, or view items by tag (fuzzy match)")
app.add_typer(check_cmd, name="check", help="Mark a habit or chore as checked for today")
app.add_typer(
    habits_cmd,
    name="habits",
    help="Show all habits and their checked off list for the last 7 days.",
)
app.add_typer(profile_cmd, name="profile", help="View or set personal profile")
app.add_typer(context_cmd, name="context", help="View or set current context")
app.add_typer(
    countdown_cmd, name="countdown", help="Add, remove, or list countdowns to target dates"
)
app.add_typer(backup_cmd, name="backup", help="Create database backup")
app.add_typer(personas_cmd, name="personas", help="View or set AI personas (roast, pepper, kim)")
app.add_typer(roast_cmd, name="roast", help="Invoke the Roast persona.")
app.add_typer(pepper_cmd, name="pepper", help="Invoke the Pepper persona.")
app.add_typer(kim_cmd, name="kim", help="Invoke the Kim persona.")
app.add_typer(chat_cmd, name="chat", help="Chat with ephemeral agent")
app.add_typer(
    items_cmd, name="items", help="Manage items (tasks and habits)."
)  # Added this registration


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


def main():
    """Check for personas before passing to typer."""
    db.init()  # Initialize database and apply migrations
    app()


if __name__ == "__main__":
    main()
