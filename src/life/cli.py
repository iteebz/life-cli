import typer

from .display import render_dashboard, render_task_list
from .sqlite import (
    add_task,
    execute_sql,
    get_context,
    get_pending_tasks,
    set_context,
    today_completed,
    weekly_momentum,
)
from .utils import complete_fuzzy, remove_fuzzy, toggle_fuzzy, update_fuzzy

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """ADHD executive function rescue system"""
    if ctx.invoked_subcommand is None:
        tasks = get_pending_tasks()
        today_count = today_completed()
        momentum = weekly_momentum()
        context = get_context()
        output = render_dashboard(tasks, today_count, momentum, context)
        typer.echo(output)


@app.command()
def task(
    content: str = typer.Argument(..., help="Task content"),
    focus: bool = typer.Option(False, help="Mark as focus task"),
    due: str = typer.Option(None, help="Due date (YYYY-MM-DD)"),
):
    """Add task"""
    add_task(content, focus=focus, due=due)
    focus_str = " [FOCUS]" if focus else ""
    due_str = f" due {due}" if due else ""
    typer.echo(f"Added: {content}{focus_str}{due_str}")


@app.command()
def remind(
    content: str = typer.Argument(..., help="Reminder content"),
):
    """Add reminder"""
    add_task(content, category="reminder")
    typer.echo(f"Added reminder: {content}")


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
    partial: str = typer.Argument(..., help="Partial reminder content for fuzzy matching"),
):
    """Complete reminder (fuzzy match, reminders only)"""
    completed = complete_fuzzy(partial, category="reminder")
    if completed:
        typer.echo(f"✓ {completed}")
    else:
        typer.echo(f"No reminder match for: {partial}")


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
def sql(
    query: str = typer.Argument(..., help="SQL query to execute"),
):
    """Execute SQL directly on tasks database"""
    try:
        results = execute_sql(query)
        if results is not None:
            for row in results:
                typer.echo(row)
        else:
            typer.echo("Query executed successfully")
    except Exception as e:
        typer.echo(f"Error: {e}")


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


@app.command()
def update(
    partial: str = typer.Argument(..., help="Partial task content for fuzzy matching"),
    content: str = typer.Option(None, help="Update content"),
    due: str = typer.Option(None, help="Update due date (YYYY-MM-DD)"),
    focus: bool = typer.Option(None, help="Set focus (true/false)"),
):
    """Update any field of a task by fuzzy match"""
    if not any([content, due is not None, focus is not None]):
        typer.echo("No updates specified")
        return

    updated_content = update_fuzzy(partial, content=content, due=due, focus=focus)
    if updated_content:
        typer.echo(f"Updated: {updated_content}")
    else:
        typer.echo(f"No match for: {partial}")


if __name__ == "__main__":
    app()
