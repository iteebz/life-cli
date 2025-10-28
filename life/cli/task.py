import typer

from ..api.items import add_item
from ..lib.ansi import ANSI

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def task(
    content: str = typer.Argument(..., help="Task content"),  # noqa: B008
    focus: bool = typer.Option(False, "--focus", "-f", help="Set task as focused"),  # noqa: B008
    due: str = typer.Option(
        None, "--due", "-d", help="Set due date (today, tomorrow, mon, YYYY-MM-DD)"
    ),  # noqa: B008
    tags: list[str] = typer.Option(None, "--tag", "-t", help="Add tags to task"),  # noqa: B008
):
    """Add task (supports focus, due date, tags, immediate completion)"""
    item_id = add_item(content, item_type="task", is_repeat=False, focus=focus, due=due, tags=tags)
    typer.echo(f"Added task: {content} {ANSI.GREY}{item_id}{ANSI.RESET}")
