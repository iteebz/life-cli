import typer

from ...lib.match import set_due

cmd = typer.Typer()


@cmd.command()
def due(
    args: list[str] = typer.Argument(..., help="Due date (YYYY-MM-DD) and item content"),  # noqa: B008
    remove: bool = typer.Option(False, "-r", "--remove", help="Remove due date"),  # noqa: B008
):
    """Set due date on item (fuzzy match)"""
    typer.echo(set_due(list(args) if args else [], remove=remove))
