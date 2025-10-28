import typer

from ..api.tasks import add_task
from ..lib.ansi import ANSI
from ..ops import _parse_due_date

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)


def task(


    content: str = typer.Argument(..., help="Task content"),  # noqa: B008


    focus: bool = typer.Option(False, "--focus", "-f", help="Set task as focused"),  # noqa: B008


    due: str = typer.Option(None, "--due", "-d", help="Set due date (today, tomorrow, mon, YYYY-MM-DD)"),  # noqa: B008


    tags: list[str] = typer.Option(None, "--tag", "-t", help="Add tags to task"),  # noqa: B008


):
    """Add task (supports focus, due date, tags, immediate completion)"""
    parsed_due = _parse_due_date(due) if due else None
    item_id = add_task(content, focus=focus, due=parsed_due, tags=tags)
    typer.echo(f"Added task: {content} {ANSI.GREY}{item_id}{ANSI.RESET}")
