import typer

from ..api import add_item

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def habit(content: str = typer.Argument(..., help="Habit content")):  # noqa: B008
    """Add daily habit (auto-resets on completion)"""
    try:
        add_item(content, tags=["habit"])
        typer.echo(f"Added habit: {content}")
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1) from None
