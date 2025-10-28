import typer

from ..api.items import delete_item, get_all_items, update_item
from ..api.tags import add_tag, remove_tag
from ..lib.ansi import ANSI
from ..lib.dates import _parse_due_date
from ..lib.render import render_item_list
from ..ops.fuzzy import find_item
from ..ops.toggle import toggle_focus

cmd = typer.Typer(help="Manage items (tasks and habits).")


@cmd.command(name="ls")
def ls_items():
    """List all items."""
    items = get_all_items()
    typer.echo(render_item_list(items))


@cmd.command(name="rm")
def rm_item(partial: str):
    """Remove an item."""
    item = find_item(partial)
    if not item:
        typer.echo(f"{ANSI.RED}Error:{ANSI.RESET} No item found matching '{partial}'")
        raise typer.Exit(code=1)
    delete_item(item.id)
    typer.echo(f"{ANSI.GREEN}Item:{ANSI.RESET} '{item.content}' removed.")


@cmd.command(name="focus")
def focus_item(partial: str):
    """Focus on an item."""
    item = find_item(partial)
    if not item:
        typer.echo(f"{ANSI.RED}Error:{ANSI.RESET} No item found matching '{partial}'")
        raise typer.Exit(code=1)
    toggle_focus(item.id, True)
    typer.echo(f"{ANSI.GREEN}Item:{ANSI.RESET} '{item.content}' focused.")


@cmd.command(name="unfocus")
def unfocus_item(partial: str):
    """Unfocus an item."""
    item = find_item(partial)
    if not item:
        typer.echo(f"{ANSI.RED}Error:{ANSI.RESET} No item found matching '{partial}'")
        raise typer.Exit(code=1)
    toggle_focus(item.id, False)
    typer.echo(f"{ANSI.GREEN}Item:{ANSI.RESET} '{item.content}' unfocused.")


@cmd.command(name="due")
def due_item(partial: str, due: str):
    """Set due date for an item."""
    item = find_item(partial)
    if not item:
        typer.echo(f"{ANSI.RED}Error:{ANSI.RESET} No item found matching '{partial}'")
        raise typer.Exit(code=1)
    parsed_date = _parse_due_date(due)
    update_item(item.id, due=parsed_date)
    typer.echo(
        f"{ANSI.GREEN}Item:{ANSI.RESET} '{item.content}' due set to {parsed_date.isoformat() if parsed_date else 'None'}."
    )


@cmd.command(name="undue")
def undue_item(partial: str):
    """Remove due date from an item."""
    item = find_item(partial)
    if not item:
        typer.echo(f"{ANSI.RED}Error:{ANSI.RESET} No item found matching '{partial}'")
        raise typer.Exit(code=1)
    update_item(item.id, due=None)
    typer.echo(f"{ANSI.GREEN}Item:{ANSI.RESET} '{item.content}' due removed.")


@cmd.command(name="tag")
def tag_item(partial: str, tag_name: str):
    """Add a tag to an item."""
    item = find_item(partial)
    if not item:
        typer.echo(f"{ANSI.RED}Error:{ANSI.RESET} No item found matching '{partial}'")
        raise typer.Exit(code=1)
    add_tag(item.id, tag_name)
    typer.echo(f"{ANSI.GREEN}Item:{ANSI.RESET} '{item.content}' tagged with '{tag_name}'.")


@cmd.command(name="untag")
def untag_item(partial: str, tag_name: str):
    """Remove a tag from an item."""
    item = find_item(partial)
    if not item:
        typer.echo(f"{ANSI.RED}Error:{ANSI.RESET} No item found matching '{partial}'")
        raise typer.Exit(code=1)
    remove_tag(item.id, tag_name)
    typer.echo(f"{ANSI.GREEN}Item:{ANSI.RESET} '{item.content}' untagged from '{tag_name}'.")


@cmd.command(name="edit")
def edit_item(partial: str, new_content: str):
    """Edit an item's content."""
    item = find_item(partial)
    if not item:
        typer.echo(f"{ANSI.RED}Error:{ANSI.RESET} No item found matching '{partial}'")
        raise typer.Exit(code=1)
    update_item(item.id, content=new_content)
    typer.echo(f"{ANSI.GREEN}Item:{ANSI.RESET} '{item.content}' updated to '{new_content}'.")
