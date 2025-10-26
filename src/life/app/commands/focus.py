import typer

from ...lib.match import toggle

cmd = typer.Typer()


@cmd.command()
def focus(
    args: list[str] = typer.Argument(..., help="Item content for fuzzy matching"),  # noqa: B008
):
    """Toggle focus on item (fuzzy match)"""
    partial = " ".join(args)
    status, content = toggle(partial)
    typer.echo(f"{status}: {content}" if status else f"No match for: {partial}")
