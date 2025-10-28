import typer

from ..api.checks import add_check
from ..api.items import get_item_by_id  # Changed from get_item

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def check(
    item_id: str = typer.Argument(..., help="The ID of the item to check"),  # noqa: B008
):
    """Mark a habit or chore as checked for today."""
    try:
        add_check(item_id)
        item = get_item_by_id(item_id)  # Changed from get_item
        if item:
            typer.echo(f"Checked: {item.content}")
        else:
            typer.echo(f"Error: Item with ID {item_id} not found after checking.")
            raise typer.Exit(code=1)
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1) from e
