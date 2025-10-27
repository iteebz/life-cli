import sys

import typer

from ...config import get_default_persona
from ...lib.claude import invoke as invoke_claude
from .backup import cmd as backup_cmd
from .chore import cmd as chore_cmd
from .context import cmd as context_cmd
from .countdown import cmd as countdown_cmd
from .done import cmd as done_cmd
from .due import cmd as due_cmd
from .focus import cmd as focus_cmd
from .habit import cmd as habit_cmd
from .personas import cmd as personas_cmd
from .profile import cmd as profile_cmd
from .rename import cmd as rename_cmd
from .rm import cmd as rm_cmd
from .tag import cmd as tag_cmd
from .task import cmd as task_cmd

KNOWN_COMMANDS = {
    "task",
    "habit",
    "chore",
    "done",
    "rm",
    "focus",
    "due",
    "rename",
    "tag",
    "profile",
    "context",
    "countdown",
    "backup",
    "personas",
    "help",
    "--help",
    "-h",
}


def _is_message(raw_args: list[str]) -> bool:
    """Check if args represent a chat message (not a command)."""
    if not raw_args:
        return False
    first_arg = raw_args[0].lower()
    return first_arg not in KNOWN_COMMANDS and not first_arg.startswith("-")


def maybe_spawn_persona() -> bool:
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
        default = get_default_persona() or "roast"
        message = " ".join(raw_args)
        invoke_claude(message, default)
        return True

    return False


def register_commands(app: typer.Typer):
    """Register all command modules with the app."""
    app.add_typer(
        task_cmd,
        name="task",
        help="Add task (supports focus, due date, tags, immediate completion)",
    )
    app.add_typer(habit_cmd, name="habit", help="Add daily habit (auto-resets on completion)")
    app.add_typer(chore_cmd, name="chore", help="Add repeating chore (auto-resets on completion)")
    app.add_typer(done_cmd, name="done", help="Mark item complete or undo completion (fuzzy match)")
    app.add_typer(rm_cmd, name="rm", help="Delete item or completed task (fuzzy match)")
    app.add_typer(focus_cmd, name="focus", help="Toggle focus status on item (fuzzy match)")
    app.add_typer(due_cmd, name="due", help="Set or remove due date on item (fuzzy match)")
    app.add_typer(rename_cmd, name="rename", help="Change item description (fuzzy match)")
    app.add_typer(tag_cmd, name="tag", help="Add, remove, or view items by tag (fuzzy match)")
    app.add_typer(profile_cmd, name="profile", help="View or set personal profile")
    app.add_typer(context_cmd, name="context", help="View or set current context")
    app.add_typer(
        countdown_cmd, name="countdown", help="Add, remove, or list countdowns to target dates"
    )
    app.add_typer(backup_cmd, name="backup", help="Create database backup")
    app.add_typer(
        personas_cmd, name="personas", help="View or set AI personas (roast, pepper, kim)"
    )
