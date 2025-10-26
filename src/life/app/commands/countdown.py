import typer

from ...config import add_countdown, get_countdowns, remove_countdown

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def countdown(
    action: str = typer.Argument(None, help="add, remove, or list"),  # noqa: B008
    name: str = typer.Argument(None, help="Countdown name"),  # noqa: B008
    date_str: str = typer.Argument(None, help="Target date (YYYY-MM-DD)"),  # noqa: B008
    emoji: str = typer.Option("📌", "-e", "--emoji", help="Emoji for countdown"),  # noqa: B008
):
    """Add, remove, or list countdowns to target dates"""
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
        add_countdown(name, date_str, emoji)
        typer.echo(f"Added countdown: {emoji} {name} on {date_str}")
    elif action == "remove":
        if not name:
            typer.echo("Error: remove requires name", err=True)
            raise typer.Exit(1)
        remove_countdown(name)
        typer.echo(f"Removed countdown: {name}")
    else:
        typer.echo(f"Error: unknown action '{action}' (use: add, remove, or list)", err=True)
        raise typer.Exit(1)
