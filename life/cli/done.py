import typer

from ..lib.ansi import ANSI
from ..ops.fuzzy import find_item
from ..ops.toggle import toggle_done

cmd = typer.Typer(help="Mark item complete or undo completion (fuzzy match).")


@cmd.callback(invoke_without_command=True)
def done(partial: str = typer.Argument(..., help="Partial match for the item to mark done/undone")):
    """Mark an item as complete/checked or uncomplete/unchecked."""
    item = find_item(partial)

    if not item:
        typer.echo(f"{ANSI.RED}Error:{ANSI.RESET} No item found matching '{partial}'")
        raise typer.Exit(code=1)

    # Determine if we are trying to undo based on the item's current state
    # For tasks, item.completed is a date string if completed, None otherwise.
    # For habits, item.completed is always None, but we check its checks table.
    # The toggle_done function will handle the habit-specific logic.
    is_undo_action = item.completed is not None

    status, content = toggle_done(partial, undo=is_undo_action)

    if status == "Checked":
        typer.echo(f"{ANSI.GREEN}Habit:{ANSI.RESET} '{content}' checked for today.")
    elif status == "Already checked":
        typer.echo(f"{ANSI.YELLOW}Habit:{ANSI.RESET} '{content}' already checked for today.")
    elif status == "Pending":
        if item.is_repeat:
            typer.echo(f"{ANSI.YELLOW}Habit:{ANSI.RESET} '{content}' unchecked for today.")
        else:
            typer.echo(f"{ANSI.YELLOW}Task:{ANSI.RESET} '{content}' marked as pending.")
    elif status == "Done":
        typer.echo(f"{ANSI.GREEN}Task:{ANSI.RESET} '{content}' marked as complete.")
    else:
        typer.echo(f"{ANSI.RED}Error:{ANSI.RESET} Unexpected status: {status} for item '{content}'")
        raise typer.Exit(code=1)
