import typer

from ..config import add_countdown as add_countdown_config
from ..config import get_countdowns, remove_countdown as remove_countdown_config


def handle_countdown(action: str | None, name: str | None, date_str: str | None, emoji: str) -> None:
    """Handle countdown add/remove/list operations."""
    if not action:
        countdowns = get_countdowns()
        if countdowns:
            for cd in sorted(countdowns, key=lambda x: x["date"]):
                typer.echo(f"{cd.get('emoji', '📌')} {cd['name']} - {cd['date']}")
        else:
            typer.echo("No countdowns set")
        return

    if action == "add":
        if not name or not date_str:
            typer.echo("Error: add requires name and date (YYYY-MM-DD)", err=True)
            raise typer.Exit(1)
        add_countdown_config(name, date_str, emoji)
        typer.echo(f"Added countdown: {emoji} {name} on {date_str}")
    elif action == "remove":
        if not name:
            typer.echo("Error: remove requires a countdown name", err=True)
            raise typer.Exit(1)
        remove_countdown_config(name)
        typer.echo(f"Removed countdown: {name}")
    else:
        typer.echo(
            f"Error: unknown action '{action}'. Use 'add', 'remove', or no argument to list.",
            err=True,
        )
        raise typer.Exit(1)
