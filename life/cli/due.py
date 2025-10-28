import typer

from ..ops.items import set_due

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def due(
    args: list[str] = typer.Argument(..., help="Due date (YYYY-MM-DD) and item content"),  # noqa: B008
    remove: bool = typer.Option(False, "-r", "--remove", help="Remove due date"),  # noqa: B008
):
    """Set or remove due date on item (fuzzy match)"""
    typer.echo(set_due(list(args) if args else [], remove=remove))
