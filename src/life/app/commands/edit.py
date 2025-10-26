import typer

from ...lib.match import edit_item

cmd = typer.Typer()


@cmd.command()
def edit(
    new_content: str = typer.Argument(..., help="New item description"),  # noqa: B008
    args: list[str] = typer.Argument(..., help="Item content for fuzzy matching"),  # noqa: B008
):
    """Edit item description (fuzzy match)"""
    typer.echo(edit_item(new_content, " ".join(args)))
