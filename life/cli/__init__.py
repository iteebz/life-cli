import sys

import typer

from .. import db
from ..api import get_pending_items, get_today_breakdown, get_today_completed, weekly_momentum
from ..config import get_context, get_profile
from ..lib.render import render_dashboard
from .backup import cmd as backup_cmd
from .chat import cmd as chat_cmd
from .check import cmd as check_cmd
from .chore import cmd as chore_cmd
from .context import cmd as context_cmd
from .countdown import cmd as countdown_cmd
from .done import done as done_command
from .due import cmd as due_cmd
from .focus import cmd as focus_cmd
from .habit import cmd as habit_cmd
from .habits import cmd as habits_cmd
from .kim import cmd as kim_cmd
from .pepper import cmd as pepper_cmd
from .personas import cmd as personas_cmd
from .profile import cmd as profile_cmd
from .rename import cmd as rename_cmd
from .roast import cmd as roast_cmd
from .rm import cmd as rm_cmd
from .tag import cmd as tag_cmd
from .task import cmd as task_cmd

app = typer.Typer()


def register_commands(app: typer.Typer):
    """Register all command modules with the app."""

    # Core Commands
    core_app = typer.Typer(name="Core Commands", help="Manage tasks, habits, and chores.")
    core_app.add_typer(task_cmd, name="task", help="Add task (supports focus, due date, tags, immediate completion)")
    core_app.add_typer(task_cmd, name="add", help="Add task (supports focus, due date, tags, immediate completion)")
    core_app.add_typer(habit_cmd, name="habit", help="Add daily habit (auto-resets on completion)")
    core_app.add_typer(chore_cmd, name="chore", help="Add repeating chore (auto-resets on completion)")
    core_app.command(name="done", help="Mark item complete or undo completion (fuzzy match)")(done_command)
    core_app.add_typer(rm_cmd, name="rm", help="Delete item or completed task (fuzzy match)")
    core_app.add_typer(focus_cmd, name="focus", help="Toggle focus status on item (fuzzy match)")
    core_app.add_typer(due_cmd, name="due", help="Set or remove due date on item (fuzzy match)")
    core_app.add_typer(rename_cmd, name="rename", help="Change item description (fuzzy match)")
    core_app.add_typer(tag_cmd, name="tag", help="Add, remove, or view items by tag (fuzzy match)")
    core_app.add_typer(check_cmd, name="check", help="Mark a habit or chore as checked for today")
    core_app.add_typer(habits_cmd, name="habits", help="Show all habits and their checked off list for the last 7 days.")
    app.add_typer(core_app)

    # Persona Commands
    persona_app = typer.Typer(name="Persona Commands", help="Interact with AI personas.")
    persona_app.add_typer(chat_cmd, name="chat", help="Chat with ephemeral agent")
    persona_app.add_typer(personas_cmd, name="personas", help="View or set AI personas (roast, pepper, kim)")
    persona_app.add_typer(roast_cmd, name="roast", help="Invoke the Roast persona.")
    persona_app.add_typer(pepper_cmd, name="pepper", help="Invoke the Pepper persona.")
    persona_app.add_typer(kim_cmd, name="kim", help="Invoke the Kim persona.")
    app.add_typer(persona_app)

    # Configuration & Utility
    config_app = typer.Typer(name="Configuration & Utility", help="Manage settings and data.")
    config_app.add_typer(profile_cmd, name="profile", help="View or set personal profile")
    config_app.add_typer(context_cmd, name="context", help="View or set current context")
    config_app.add_typer(countdown_cmd, name="countdown", help="Add, remove, or list countdowns to target dates")
    config_app.add_typer(backup_cmd, name="backup", help="Create database backup")
    app.add_typer(config_app)


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


register_commands(app)


def main():
    """Check for personas before passing to typer."""
    db.init()  # Initialize database and apply migrations
    app()


if __name__ == "__main__":
    main()
