import typer

from ...lib.ops import edit_item

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def rename(
    new_content: str = typer.Argument(..., help="New item description"),  # noqa: B008
    args: list[str] = typer.Argument(..., help="Item content for fuzzy matching"),  # noqa: B008
):
    """Change item description (fuzzy match)"""
    typer.echo(edit_item(new_content, " ".join(args)))
