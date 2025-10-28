import typer

from ..lib.match import find_item
from ..ops.items import update

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def rename(
    from_args: list[str] = typer.Argument(  # noqa: B008
        ..., help="Content to fuzzy match for the item to rename"
    ),
    to_content: str = typer.Argument(..., help="The exact new content for the item"),  # noqa: B008
):
    """Rename an item using fuzzy matching for 'from' and exact match for 'to'"""
    if not to_content:
        typer.echo("Error: 'to' content cannot be empty.")
        raise typer.Exit(code=1)

    partial_from = " ".join(from_args)
    item_to_rename = find_item(partial_from)

    if not item_to_rename:
        typer.echo(f"No fuzzy match found for: '{partial_from}'")
        raise typer.Exit(code=1)

    if item_to_rename.content == to_content:
        typer.echo(f"Error: Cannot rename '{item_to_rename.content}' to itself.")
        raise typer.Exit(code=1)

    update(partial_from, content=to_content)

    typer.echo(f"Updated: '{item_to_rename.content}' → '{to_content}'")
