import itertools
import os
import subprocess
import sys
import threading
import time

import typer

from . import sqlite as db
from .display import render_dashboard
from .personas import get_persona
from .sqlite import (
    add_tag,
    add_task,
    get_context,
    get_default_persona,
    get_profile,
    get_pending_tasks,
    get_tasks_by_tag,
    get_today_completed,
    set_context,
    set_default_persona,
    set_profile,
    today_completed,
    uncomplete_task,
    weekly_momentum,
)
from .utils import complete_fuzzy, remove_fuzzy, toggle_fuzzy, uncomplete_fuzzy

DATABASE = "~/.life/store.db"

app = typer.Typer()


class Spinner:
    """Simple CLI spinner for async feedback."""

    def __init__(self, persona: str = "roast"):
        self.stop_event = threading.Event()
        self.spinner_frames = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
        self.persona = persona
        self.thread = None

    def _animate(self):
        """Run spinner animation in background thread."""
        actions = {"roast": "roasting", "pepper": "peppering", "kim": "investigating"}
        action = actions.get(self.persona, "thinking")
        while not self.stop_event.is_set():
            frame = next(self.spinner_frames)
            sys.stderr.write(f"\r{frame} {action}... ")
            sys.stderr.flush()
            time.sleep(0.1)
        sys.stderr.write("\r" + " " * 30 + "\r")
        sys.stderr.flush()

    def start(self):
        """Start the spinner."""
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the spinner."""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=0.5)


def _build_roast_context() -> str:
    """Build context for ephemeral claude roast."""
    tasks = get_pending_tasks()
    today_count = today_completed()
    momentum = weekly_momentum()
    life_context = get_context()
    today_items = get_today_completed()
    return render_dashboard(tasks, today_count, momentum, life_context, today_items)


def _known_commands() -> set[str]:
    """Return set of known CLI commands."""
    return {
        "task",
        "habit",
        "chore",
        "done",
        "check",
        "rm",
        "focus",
        "due",
        "edit",
        "tag",
        "profile",
        "context",
        "backup",
        "personas",
        "help",
        "--help",
        "-h",
    }


def _is_message(raw_args: list[str]) -> bool:
    """Detect if args represent a chat message (not a command)."""
    if not raw_args:
        return False
    first_arg = raw_args[0].lower()
    if first_arg in _known_commands():
        return False
    if first_arg.startswith("-"):
        return False
    return True


def _spawn_persona(message: str, persona: str = "roast") -> None:
    """Spawn ephemeral claude persona."""
    from .lib.ansi import md_to_ansi

    persona_instructions = get_persona(persona)
    profile = get_profile()
    
    profile_section = f"PROFILE:\n{profile}\n\n" if profile else ""
    
    task_prompt = f"""{persona_instructions}

{profile_section}---
USER MESSAGE: {message}

RESPONSE PROTOCOL:
- Be concise and direct
- Use `life` CLI output to assess current state
- Provide actionable analysis or next steps
- Format markdown for bold/emphasis where helpful"""

    env = os.environ.copy()
    env["LIFE_PERSONA"] = persona

    spinner = Spinner(persona)
    spinner.start()

    result = subprocess.run(
        ["claude", "--model", "claude-haiku-4-5", "-p", task_prompt, "--allowedTools", "Bash"],
        env=env,
        capture_output=True,
        text=True,
    )

    spinner.stop()
    from .lib.ansi import ANSI, PERSONA_COLORS

    formatted = md_to_ansi(result.stdout)
    color = PERSONA_COLORS.get(persona, ANSI.WHITE)
    header = f"\n{ANSI.BOLD}{color}[{persona}]:{ANSI.RESET}\n\n"
    sys.stdout.write(header + formatted + "\n")
    sys.stdout.flush()
    sys.exit(result.returncode)


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
            _spawn_persona(message, persona)
            return True
    elif _is_message(raw_args):
        default = get_default_persona()
        if default:
            message = " ".join(raw_args)
            _spawn_persona(message, default)
            return True

    return False


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Ephemeral life agent"""
    if ctx.invoked_subcommand is None:
        tasks = get_pending_tasks()
        today_count = today_completed()
        momentum = weekly_momentum()
        life_context = get_context()
        today_items = get_today_completed()
        typer.echo(render_dashboard(tasks, today_count, momentum, life_context, today_items))


@app.command()
def task(
    content: str = typer.Argument(..., help="Task content"),
    focus: bool = typer.Option(False, "-f", "--focus", help="Mark as focus task"),
    due: str = typer.Option(None, "-d", "--due", help="Due date (YYYY-MM-DD)"),
    done: bool = typer.Option(False, "-x", "--done", help="Immediately mark task as done"),
):
    """Add task"""
    add_task(content, focus=focus, due=due)
    focus_str = " [FOCUS]" if focus else ""
    due_str = f" due {due}" if due else ""

    if done:
        from .utils import complete_fuzzy

        complete_fuzzy(content)
        typer.echo(f"Added & completed: {content}{focus_str}{due_str}")
    else:
        typer.echo(f"Added: {content}{focus_str}{due_str}")


@app.command()
def habit(
    content: str = typer.Argument(..., help="Habit content"),
):
    """Add habit"""
    add_task(content, category="habit")
    typer.echo(f"Added habit: {content}")


@app.command()
def chore(
    content: str = typer.Argument(..., help="Chore content"),
):
    """Add chore"""
    add_task(content, category="chore")
    typer.echo(f"Added chore: {content}")


@app.command()
def done(
    args: list[str] = typer.Argument(None, help="Task content for fuzzy matching"),
    undo: bool = typer.Option(False, "-u", "--undo", "-r", "--remove", help="Undo task completion"),
):
    """Complete task (fuzzy match)"""
    if not args:
        typer.echo("No task specified")
        return
    partial = " ".join(args)
    if undo:
        uncompleted = uncomplete_fuzzy(partial)
        if uncompleted:
            typer.echo(f"Uncompleted: {uncompleted}")
        else:
            typer.echo(f"No match for: {partial}")
    else:
        completed = complete_fuzzy(partial)
        if completed:
            typer.echo(f"Completed: {completed}")
        else:
            typer.echo(f"No match for: {partial}")


@app.command()
def check(
    args: list[str] = typer.Argument(..., help="Habit/chore content for fuzzy matching"),
    when: str = typer.Option(None, "-w", "--when", help="Check date (YYYY-MM-DD), defaults to today"),
):
    """Check habit or chore (fuzzy match)"""
    from .sqlite import check_reminder, get_pending_tasks
    from .utils import find_task

    partial = " ".join(args)
    task = find_task(partial, category="habit")
    if not task:
        task = find_task(partial, category="chore")
    if task:
        check_reminder(task[0], when)
        refresh = [t for t in get_pending_tasks() if t[0] == task[0]]
        if refresh:
            count, target = refresh[0][7], refresh[0][8]
            typer.echo(f"✓ {task[1]} ({count}/{target})")
        else:
            typer.echo(f"✓ {task[1]} - DONE!")
    else:
        typer.echo(f"No habit/chore match for: {partial}")


@app.command()
def rm(
    args: list[str] = typer.Argument(..., help="Task content for fuzzy matching"),
):
    """Remove task (fuzzy match)"""
    partial = " ".join(args)
    removed = remove_fuzzy(partial)
    if removed:
        typer.echo(f"Removed: {removed}")
    else:
        typer.echo(f"No match for: {partial}")


@app.command()
def focus(
    args: list[str] = typer.Argument(..., help="Task content for fuzzy matching"),
):
    """Toggle focus on task (fuzzy match)"""
    partial = " ".join(args)
    status, content = toggle_fuzzy(partial)
    if status:
        typer.echo(f"{status}: {content}")
    else:
        typer.echo(f"No match for: {partial}")


@app.command()
def due(
    args: list[str] = typer.Argument(..., help="Due date (YYYY-MM-DD) and task content"),
    remove: bool = typer.Option(False, "-r", "--remove", help="Remove due date"),
):
    """Set due date on task (fuzzy match)"""
    from .sqlite import update_task
    from .utils import find_task
    
    import re
    
    if not args:
        typer.echo("Due date and task required")
        return
    
    date_str = None
    task_args = args
    
    if not remove and len(args) > 0:
        if re.match(r'^\d{4}-\d{2}-\d{2}$', args[0]):
            date_str = args[0]
            task_args = args[1:]
    
    if not task_args:
        typer.echo("Task name required")
        return
    
    partial = " ".join(task_args)
    task = find_task(partial)
    if task:
        if remove:
            update_task(task[0], due=None)
            typer.echo(f"Due date removed: {task[1]}")
        else:
            if not date_str:
                typer.echo("Due date required (YYYY-MM-DD) or use -r/--remove to clear")
                return
            update_task(task[0], due=date_str)
            typer.echo(f"Due: {task[1]} on {date_str}")
    else:
        typer.echo(f"No match for: {partial}")


@app.command()
def edit(
    new_content: str = typer.Argument(..., help="New task description"),
    args: list[str] = typer.Argument(..., help="Task content for fuzzy matching"),
):
    """Edit task description (fuzzy match)"""
    from .sqlite import update_task
    from .utils import find_task

    partial = " ".join(args)
    task = find_task(partial)
    if task:
        update_task(task[0], content=new_content)
        typer.echo(f"Updated: {task[1]} → {new_content}")
    else:
        typer.echo(f"No match for: {partial}")


@app.command()
def tag(
    tag_name: str = typer.Argument(..., help="Tag name"),
    args: list[str] = typer.Argument(None, help="Task content for fuzzy matching"),
    remove: bool = typer.Option(False, "--remove", "-r", help="Remove tag instead of adding"),
):
    """Add/remove tag to/from task (fuzzy match), or view tasks by tag"""
    if args:
        from .sqlite import remove_tag
        from .utils import find_task

        partial = " ".join(args)
        task = find_task(partial)
        if task:
            if remove:
                remove_tag(task[0], tag_name)
                typer.echo(f"Untagged: {task[1]} ← #{tag_name}")
            else:
                add_tag(task[0], tag_name)
                typer.echo(f"Tagged: {task[1]} → #{tag_name}")
        else:
            typer.echo(f"No match for: {partial}")
    else:
        tasks = get_tasks_by_tag(tag_name)
        if tasks:
            from .display import render_task_list

            typer.echo(f"\n{tag_name.upper()} ({len(tasks)}):")
            typer.echo(render_task_list(tasks))
        else:
            typer.echo(f"No tasks tagged with #{tag_name}")


@app.command()
def profile(
    profile_text: str = typer.Argument(None, help="Profile to set"),
):
    """View or update your profile"""
    if profile_text:
        set_profile(profile_text)
        typer.echo(f"Profile: {profile_text}")
    else:
        prof = get_profile()
        typer.echo(f"Profile: {prof if prof else '(none)'}")


@app.command()
def context(
    context_text: str = typer.Argument(None, help="Context text to set"),
):
    """View or update your context"""
    if context_text:
        set_context(context_text)
        typer.echo(f"Context: {context_text}")
    else:
        ctx = get_context()
        typer.echo(f"Context: {ctx if ctx else '(none)'}")


@app.command()
def personas(
    name: str = typer.Argument(None, help="Persona name (roast, pepper, kim)"),
    default: bool = typer.Option(False, "-d", "--default", help="Set as default persona"),
):
    """Show available personas or view/set a specific persona"""
    descriptions = {
        "roast": "The mirror. Call out patterns, push back on bullshit.",
        "pepper": "Pepper Potts energy. Optimistic enabler. Unlock potential.",
        "kim": "Lieutenant Kim Kitsuragi. Methodical clarity. Work the case.",
    }
    
    if not name:
        typer.echo("Available personas:")
        for p in ("roast", "pepper", "kim"):
            typer.echo(f"  {p:8} - {descriptions[p]}")
        return
    
    aliases = {"kitsuragi": "kim"}
    resolved_name = aliases.get(name, name)
    if resolved_name not in ("roast", "pepper", "kim"):
        typer.echo(f"Unknown persona: {resolved_name}", err=True)
        raise typer.Exit(1)
    
    if default:
        set_default_persona(resolved_name)
        typer.echo(f"Default persona set to: {resolved_name}")
    else:
        try:
            persona = get_persona(resolved_name)
            typer.echo(persona)
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)


@app.command()
def backup():
    """Backup database"""
    backup_path = db.backup()
    typer.echo(f"{backup_path}")


def main_with_personas():
    """Wrapper that checks for personas before passing to typer."""
    if _maybe_spawn_persona():
        sys.exit(0)
    app()


if __name__ == "__main__":
    main_with_personas()
