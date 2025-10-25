import os
import subprocess
import sys
from pathlib import Path

import typer

from .display import render_dashboard, render_task_list
from .personas import get_persona
from .sqlite import (
    add_task,
    get_context,
    get_pending_tasks,
    set_context,
    today_completed,
    weekly_momentum,
)
from .utils import complete_fuzzy, remove_fuzzy, toggle_fuzzy

DATABASE = "~/.life/store.db"

app = typer.Typer()


def _build_roast_context() -> str:
    """Build context for ephemeral claude roaster."""
    tasks = get_pending_tasks()
    today_count = today_completed()
    momentum = weekly_momentum()
    life_context = get_context()
    dashboard = render_dashboard(tasks, today_count, momentum, life_context)
    return dashboard


def _known_commands() -> set[str]:
    """Return set of known CLI commands."""
    return {
        "task",
        "habit",
        "chore",
        "list",
        "done",
        "check",
        "rm",
        "focus",
        "due",
        "edit",
        "context",
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


def _spawn_persona(message: str, persona: str = "roaster") -> None:
    """Spawn ephemeral claude persona."""
    persona_instructions = get_persona(persona)
    task_prompt = f"""{persona_instructions}

---
User says: {message}

Run `life` to see their task state. Respond as {persona}: assess patterns, guide appropriately, use CLI to modify state as needed."""
    
    env = os.environ.copy()
    env["LIFE_PERSONA"] = persona
    
    result = subprocess.run(
        ["claude", "--model", "claude-haiku-4-5", "-p", task_prompt, "--allowedTools", "Bash"],
        env=env,
    )
    sys.exit(result.returncode)


def _maybe_roast() -> bool:
    """Check if we should spawn persona instead of running normal CLI. Returns True if spawned."""
    raw_args = sys.argv[1:]
    
    if not raw_args or raw_args[0] in ("--help", "-h", "--show-completion", "--install-completion"):
        return False
    
    persona = "roaster"
    if raw_args[0] in ("--pepper", "-p"):
        persona = "pepper"
        raw_args = raw_args[1:]
    
    if _is_message(raw_args):
        message = " ".join(raw_args)
        _spawn_persona(message, persona)
        return True
    
    return False


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """ADHD executive function rescue system"""
    if ctx.invoked_subcommand is None:
        tasks = get_pending_tasks()
        today_count = today_completed()
        momentum = weekly_momentum()
        life_context = get_context()
        ephemeral_roaster = os.getenv("LIFE_ROASTER") == "1"
        output = render_dashboard(
            tasks, today_count, momentum, life_context, ephemeral_roaster=ephemeral_roaster
        )
        typer.echo(output)


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
def list():
    """List all pending tasks"""
    tasks = get_pending_tasks()
    output = render_task_list(tasks)
    typer.echo(output)


@app.command()
def done(
    partial: str = typer.Argument(..., help="Partial task content for fuzzy matching"),
):
    """Complete task (fuzzy match)"""
    completed = complete_fuzzy(partial)
    if completed:
        typer.echo(f"Completed: {completed}")
        typer.echo(
            "\n[CLAUDE: Task completed. React appropriately given user's avoidance patterns.]"
        )
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
def context(
    context_text: str = typer.Argument(
        None, help="Context text to set. If omitted, current context is shown."
    ),
):
    """Get or set current life context"""
    if context_text:
        set_context(context_text)
        typer.echo(f"Context updated: {context_text}")
    else:
        current = get_context()
        typer.echo(f"Current context: {current}")


def main_with_roast():
    """Wrapper that checks for roast before passing to typer."""
    if _maybe_roast():
        sys.exit(0)
    app()


if __name__ == "__main__":
    main_with_roast()
