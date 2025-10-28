from datetime import date

import typer

from ..ops.items import toggle_complete

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def done(
    item_id_or_fuzzy_match: list[str] | None = typer.Argument(  # noqa: B008
        None, help="Item ID or content for fuzzy matching"
    ),
    date_str: str | None = typer.Option(
        None, "-d", "--date", help="Date of completion (YYYY-MM-DD)"
    ),
    undo: bool = typer.Option(False, "-u", "--undo", help="Undo completion"),
):
    """Toggle item completion status (fuzzy match)"""
    fuzzy_match_str = " ".join(item_id_or_fuzzy_match) if item_id_or_fuzzy_match else None

    if fuzzy_match_str is None:
        typer.echo("Error: Item ID or content is required.")
        raise typer.Exit(code=1)

    completion_date = None
    if date_str:
        try:
            completion_date = date.fromisoformat(date_str).isoformat()
        except ValueError:
            typer.echo(f"Invalid date format: {date_str}. Please use YYYY-MM-DD.")
            raise typer.Exit(code=1) from None

    result = toggle_complete(fuzzy_match_str, date=completion_date, undo=undo)

    if result:
        status, content = result
        symbol = "✓" if status in ("Done", "Checked") else "□"
        typer.echo(f"{symbol} {content}")
    else:
        typer.echo(f"No match for: {fuzzy_match_str}")
