import typer

from ...core.item import add_habit

cmd = typer.Typer()


@cmd.command()
def habit(content: str = typer.Argument(..., help="Habit content")):  # noqa: B008
    """Add habit"""
    typer.echo(add_habit(content))
