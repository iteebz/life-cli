import typer

from ..api.items import get_item
from ..api.tags import add_tag, get_items_by_tag, remove_tag

cmd = typer.Typer()


@cmd.command(name="add")
def add(
    tag: str = typer.Argument(..., help="Tag to add"),
    item_id: str = typer.Argument(None, help="Item ID to tag"),
):
    """Add a tag to an item."""
    if item_id:
        item = get_item(item_id)
        if item:
            add_tag(item.id, tag)
            typer.echo(f"Added tag '{tag}' to item '{item.content}'")
        else:
            typer.echo(f"Item with ID '{item_id}' not found.")
    else:
        typer.echo("Please provide an item ID.")


@cmd.command(name="rm")
def rm(
    tag: str = typer.Argument(..., help="Tag to remove"),
    item_id: str = typer.Argument(None, help="Item ID to untag"),
):
    """Remove a tag from an item."""
    if item_id:
        item = get_item(item_id)
        if item:
            remove_tag(item.id, tag)
            typer.echo(f"Removed tag '{tag}' from item '{item.content}'")
        else:
            typer.echo(f"Item with ID '{item_id}' not found.")
    else:
        typer.echo("Please provide an item ID.")


@cmd.command(name="ls")
def ls(tag: str = typer.Argument(None, help="Tag to list items for")):
    """List items by tag, or all tags if no tag is specified."""
    if tag:
        items = get_items_by_tag(tag)
        if items:
            typer.echo(f"Items with tag '{tag}':")
            for item in items:
                typer.echo(f"- {item.content} (ID: {item.id})")
        else:
            typer.echo(f"No items found with tag '{tag}'.")
    else:
        # This part needs to be implemented if we want to list all tags
        typer.echo("Listing all tags is not yet implemented.")


def manage_tag(item_id: str, tag: str, action: str):
    """Manage tags for an item."""
    item = get_item(item_id)
    if not item:
        typer.echo(f"Item with ID '{item_id}' not found.")
        return

    if action == "add":
        add_tag(item.id, tag)
        typer.echo(f"Added tag '{tag}' to item '{item.content}'")
    elif action == "remove":
        remove_tag(item.id, tag)
        typer.echo(f"Removed tag '{tag}' from item '{item.content}'")
    else:
        typer.echo(f"Unknown action: {action}. Use 'add' or 'remove'.")
