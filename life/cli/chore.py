import typer

from ..api import add_item

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def chore(content: str = typer.Argument(..., help="Chore content")):  # noqa: B008
    """Add repeating chore (auto-resets on completion)"""
    try:
        add_item(content, tags=["chore"])
        typer.echo(f"Added chore: {content}")
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1) from None
