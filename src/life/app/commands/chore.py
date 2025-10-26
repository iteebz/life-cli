import typer

from ...core.item import add_chore

cmd = typer.Typer()


@cmd.command()
def chore(content: str = typer.Argument(..., help="Chore content")):  # noqa: B008
    """Add chore"""
    typer.echo(add_chore(content))
