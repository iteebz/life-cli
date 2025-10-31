import typer

from ..config import add_date as add_date_config
from ..config import get_dates, remove_date as remove_date_config


def handle_dates(action: str | None, name: str | None, date_str: str | None, emoji: str) -> None:
    """Handle dates add/remove/list operations."""
    if not action:
        dates = get_dates()
        if dates:
            for d in sorted(dates, key=lambda x: x["date"]):
                typer.echo(f"{d.get('emoji', '📌')} {d['name']} - {d['date']}")
        else:
            typer.echo("No dates set")
        return

    if action == "add":
        if not name or not date_str:
            typer.echo("Error: add requires name and date (YYYY-MM-DD)", err=True)
            raise typer.Exit(1)
        add_date_config(name, date_str, emoji)
        typer.echo(f"Added date: {emoji} {name} on {date_str}")
    elif action == "remove":
        if not name:
            typer.echo("Error: remove requires a date name", err=True)
            raise typer.Exit(1)
        remove_date_config(name)
        typer.echo(f"Removed date: {name}")
    else:
        typer.echo(
            f"Error: unknown action '{action}'. Use 'add', 'remove', or no argument to list.",
            err=True,
        )
        raise typer.Exit(1)
