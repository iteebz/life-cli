import typer

from ...core.item import add_chore

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def chore(content: str = typer.Argument(..., help="Chore content")):  # noqa: B008
    """Add repeating chore (auto-resets on completion)"""
    typer.echo(add_chore(content))
