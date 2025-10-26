import typer

from ...core.item import add_habit

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def habit(content: str = typer.Argument(..., help="Habit content")):  # noqa: B008
    """Add daily habit (auto-resets on completion)"""
    typer.echo(add_habit(content))
