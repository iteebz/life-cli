import re
from datetime import date, timedelta

import typer

from ...core.item import add_task


def _parse_due_date(date_input: str) -> str | None:
    """Parse flexible date input to YYYY-MM-DD format.

    Accepts:
    - today, tomorrow
    - Day names (mon, tue, wed, thu, fri, sat, sun) - finds next occurrence
    - ISO format (YYYY-MM-DD)
    """
    if not date_input:
        return None

    date_input = date_input.lower().strip()
    today = date.today()

    if date_input == "today":
        return today.isoformat()

    if date_input == "tomorrow":
        return (today + timedelta(days=1)).isoformat()

    day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
    if date_input in day_map:
        target_day = day_map[date_input]
        current_day = today.weekday()
        days_ahead = target_day - current_day
        if days_ahead <= 0:
            days_ahead += 7
        return (today + timedelta(days=days_ahead)).isoformat()

    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_input):
        return date_input

    return None


def task(
    content: str = typer.Argument(..., help="Task content"),  # noqa: B008
    focus: bool = typer.Option(False, "-f", "--focus", help="Mark as focus item"),  # noqa: B008
    due: str = typer.Option(
        None, "-d", "--due", help="Due date (today, tomorrow, day name, or YYYY-MM-DD)"
    ),  # noqa: B008
    done: bool = typer.Option(False, "-x", "--done", help="Immediately mark item as done"),  # noqa: B008
    tag: list[str] = typer.Option(None, "-t", "--tag", help="Add tags to item"),  # noqa: B008
):
    """Add task (supports focus, due date, tags, immediate completion)"""
    due_date = _parse_due_date(due) if due else None
    if due and not due_date:
        typer.echo(f"Invalid due date: {due}")
        raise typer.Exit(1)

    typer.echo(add_task(content, focus=focus, due=due_date, done=done, tags=tag))
