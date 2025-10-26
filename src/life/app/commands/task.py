import typer

from ...core.item import add_task

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def task(
    args: list[str] = typer.Argument(..., help="Task content"),  # noqa: B008
    focus: bool = typer.Option(False, "-f", "--focus", help="Mark as focus item"),  # noqa: B008
    due: str = typer.Option(None, "-d", "--due", help="Due date (YYYY-MM-DD)"),  # noqa: B008
    done: bool = typer.Option(False, "-x", "--done", help="Immediately mark item as done"),  # noqa: B008
    tag: list[str] = typer.Option(None, "-t", "--tag", help="Add tags to item"),  # noqa: B008
):
    """Add task (supports focus, due date, tags, immediate completion)"""
    typer.echo(add_task(" ".join(args), focus=focus, due=due, done=done, tags=tag))
