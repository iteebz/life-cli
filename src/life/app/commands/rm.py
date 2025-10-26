import typer

from ...lib.match import remove

cmd = typer.Typer()


@cmd.command()
def rm(
    args: list[str] = typer.Argument(..., help="Item content for fuzzy matching"),  # noqa: B008
):
    """Remove item (fuzzy match)"""
    partial = " ".join(args)
    result = remove(partial)
    typer.echo(f"Removed: {result}" if result else f"No match for: {partial}")
