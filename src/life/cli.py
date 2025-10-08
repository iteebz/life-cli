import click

from .display import render_dashboard, render_task_list
from .storage import (
    add_task,
    execute_sql,
    get_context,
    get_pending_tasks,
    set_context,
    today_completed,
    weekly_momentum,
)
from .utils import complete_fuzzy, remove_fuzzy, toggle_fuzzy, update_fuzzy


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """ADHD executive function rescue system"""
    if ctx.invoked_subcommand is None:
        tasks = get_pending_tasks()
        today_count = today_completed()
        momentum = weekly_momentum()
        context = get_context()
        output = render_dashboard(tasks, today_count, momentum, context)
        click.echo(output)


@main.command()
@click.argument("content")
@click.option("--focus", is_flag=True, help="Mark as focus task")
@click.option("--due", help="Due date (YYYY-MM-DD)")
def task(content, focus, due):
    """Add task"""
    add_task(content, focus=focus, due=due)
    focus_str = " [FOCUS]" if focus else ""
    due_str = f" due {due}" if due else ""
    click.echo(f"Added: {content}{focus_str}{due_str}")


@main.command()
@click.argument("content")
def remind(content):
    """Add reminder"""
    add_task(content, category="reminder")
    click.echo(f"Added reminder: {content}")


@main.command()
def list():
    """List all pending tasks"""
    tasks = get_pending_tasks()
    output = render_task_list(tasks)
    click.echo(output)


@main.command()
@click.argument("partial")
def done(partial):
    """Complete task (fuzzy match)"""
    completed = complete_fuzzy(partial)
    if completed:
        click.echo(f"Completed: {completed}")
        click.echo(
            "\n[CLAUDE: Task completed. React appropriately given user's avoidance patterns.]"
        )
    else:
        click.echo(f"No match for: {partial}")


@main.command()
@click.argument("partial")
def rm(partial):
    """Remove task (fuzzy match)"""
    removed = remove_fuzzy(partial)
    if removed:
        click.echo(f"Removed: {removed}")
    else:
        click.echo(f"No match for: {partial}")


@main.command()
@click.argument("partial")
def focus(partial):
    """Toggle focus on task (fuzzy match)"""
    status, content = toggle_fuzzy(partial)
    if status:
        click.echo(f"{status}: {content}")
    else:
        click.echo(f"No match for: {partial}")


@main.command()
@click.argument("query")
def sql(query):
    """Execute SQL directly on tasks database"""
    try:
        results = execute_sql(query)
        if results is not None:
            for row in results:
                click.echo(row)
        else:
            click.echo("Query executed successfully")
    except Exception as e:
        click.echo(f"Error: {e}")


@main.command()
@click.argument("context_text", required=False)
def context(context_text):
    """Get or set current life context"""
    if context_text:
        set_context(context_text)
        click.echo(f"Context updated: {context_text}")
    else:
        current = get_context()
        click.echo(f"Current context: {current}")


@main.command()
@click.argument("partial")
@click.option("--content", help="Update content")
@click.option("--due", help="Update due date (YYYY-MM-DD)")
@click.option("--focus", type=bool, help="Set focus (true/false)")
def update(partial, content, due, focus):
    """Update any field of a task by fuzzy match"""
    if not any([content, due is not None, focus is not None]):
        click.echo("No updates specified")
        return

    updated_content = update_fuzzy(partial, content=content, due=due, focus=focus)
    if updated_content:
        click.echo(f"Updated: {updated_content}")
    else:
        click.echo(f"No match for: {partial}")


if __name__ == "__main__":
    main()
