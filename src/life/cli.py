import itertools
import os
import subprocess
import sys
import threading
import time

import typer

from .display import render_dashboard
from .personas import get_persona, PERSONAS
from . import sqlite as db
from .sqlite import (
    add_tag,
    add_task,
    get_context,
    get_neurotype,
    get_pending_tasks,
    get_tasks_by_tag,
    get_today_completed,
    set_context,
    set_neurotype,
    today_completed,
    weekly_momentum,
)
from .utils import complete_fuzzy, remove_fuzzy, toggle_fuzzy

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
            sys.stdout.write(f"\r{frame} {action}... ")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r")
        sys.stdout.flush()

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
        "backup",
        "roast",
        "pepper",
        "kim",
        "help",
        "--help",
        "-h",
    }


def _is_message(raw_args: list[str]) -> bool:
    """Detect if args represent a chat message (not a command)."""
    if not raw_args:
        return False
    first_arg = raw_args[0].lower()
    return first_arg not in _known_commands()


def _spawn_persona(message: str, persona: str = "roast") -> None:
    """Spawn ephemeral claude persona."""
    persona_instructions = get_persona(persona)
    task_prompt = f"""{persona_instructions}

---
User says: {message}

Run `life` to see their task state. Respond as {persona}: assess patterns, guide appropriately, use CLI to modify state as needed."""

    env = os.environ.copy()
    env["LIFE_PERSONA"] = persona

    spinner = Spinner(persona)
    spinner.start()

    result = subprocess.run(
        ["claude", "--model", "claude-haiku-4-5", "-p", task_prompt, "--allowedTools", "Bash"],
        env=env,
    )

    spinner.stop()
    sys.stdout.write("\n")
    sys.stdout.flush()
    sys.exit(result.returncode)


def _maybe_spawn_persona() -> bool:
    """Check if we should spawn persona. Returns True if spawned."""
    raw_args = sys.argv[1:]

    if not raw_args or raw_args[0] in ("--help", "-h", "--show-completion", "--install-completion"):
        return False

    if raw_args[0] == "roast":
        persona = "roast"
        raw_args = raw_args[1:]
        if _is_message(raw_args):
            message = " ".join(raw_args)
            _spawn_persona(message, persona)
            return True
    elif raw_args[0] == "pepper":
        persona = "pepper"
        raw_args = raw_args[1:]
        if _is_message(raw_args):
            message = " ".join(raw_args)
            _spawn_persona(message, persona)
            return True
    elif raw_args[0] == "kim":
        persona = "kim"
        raw_args = raw_args[1:]
        if _is_message(raw_args):
            message = " ".join(raw_args)
            _spawn_persona(message, persona)
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
    focus: bool = typer.Option(False, help="Mark as focus task"),
    due: str = typer.Option(None, help="Due date (YYYY-MM-DD)"),
    done: bool = typer.Option(False, help="Immediately mark task as done"),
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
    partial: str = typer.Argument(..., help="Partial task content for fuzzy matching"),
):
    """Complete task (fuzzy match)"""
    completed = complete_fuzzy(partial)
    if completed:
        typer.echo(f"Completed: {completed}")
    else:
        typer.echo(f"No match for: {partial}")


@app.command()
def check(
    partial: str = typer.Argument(..., help="Partial habit/chore content for fuzzy matching"),
    when: str = typer.Option(None, "--when", help="Check date (YYYY-MM-DD), defaults to today"),
):
    """Check habit or chore (fuzzy match)"""
    from .sqlite import check_reminder, get_pending_tasks
    from .utils import find_task

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
    partial: str = typer.Argument(..., help="Partial task content for fuzzy matching"),
):
    """Remove task (fuzzy match)"""
    removed = remove_fuzzy(partial)
    if removed:
        typer.echo(f"Removed: {removed}")
    else:
        typer.echo(f"No match for: {partial}")


@app.command()
def focus(
    partial: str = typer.Argument(..., help="Partial task content for fuzzy matching"),
):
    """Toggle focus on task (fuzzy match)"""
    status, content = toggle_fuzzy(partial)
    if status:
        typer.echo(f"{status}: {content}")
    else:
        typer.echo(f"No match for: {partial}")


@app.command()
def due(
    partial: str = typer.Argument(..., help="Partial task content for fuzzy matching"),
    date_str: str = typer.Argument(..., help="Due date (YYYY-MM-DD)"),
):
    """Set due date on task (fuzzy match)"""
    from .sqlite import update_task
    from .utils import find_task

    task = find_task(partial)
    if task:
        update_task(task[0], due=date_str)
        typer.echo(f"Due: {task[1]} on {date_str}")
    else:
        typer.echo(f"No match for: {partial}")


@app.command()
def edit(
    partial: str = typer.Argument(..., help="Partial task content for fuzzy matching"),
    new_content: str = typer.Argument(..., help="New task description"),
):
    """Edit task description (fuzzy match)"""
    from .sqlite import update_task
    from .utils import find_task

    task = find_task(partial)
    if task:
        update_task(task[0], content=new_content)
        typer.echo(f"Updated: {task[1]} → {new_content}")
    else:
        typer.echo(f"No match for: {partial}")


@app.command()
def tag(
    tag_name: str = typer.Argument(..., help="Tag name"),
    partial: str = typer.Argument(None, help="Partial task content for fuzzy matching"),
):
    """Add tag to task (fuzzy match), or view tasks by tag"""
    if partial:
        from .utils import find_task

        task = find_task(partial)
        if task:
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
    context_text: str = typer.Argument(None, help="Context text to set"),
    neurotype: str = typer.Option(None, "--neurotype", "-n", help="Neurotype to set"),
):
    """View or update your profile"""
    if context_text or neurotype:
        if context_text:
            set_context(context_text)
            typer.echo(f"Context: {context_text}")
        if neurotype:
            set_neurotype(neurotype)
            typer.echo(f"Neurotype: {neurotype}")
    else:
        ctx = get_context()
        nt = get_neurotype()
        typer.echo("Your profile:")
        typer.echo(f"  Context: {ctx if ctx else '(none)'}")
        typer.echo(f"  Neurotype: {nt if nt else '(none)'}")


@app.command()
def personas(
    name: str = typer.Argument(..., help="Persona name (roast, pepper, kim)"),
):
    """Show persona instructions"""
    try:
        persona = get_persona(name)
        typer.echo(persona)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def backup():
    """Backup database"""
    backup_path = db.backup()
    typer.echo(f"{backup_path / 'store.db'}")


def main_with_personas():
    """Wrapper that checks for personas before passing to typer."""
    if _maybe_spawn_persona():
        sys.exit(0)
    app()


if __name__ == "__main__":
    main_with_personas()
