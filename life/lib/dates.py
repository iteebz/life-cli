from datetime import date, timedelta

from ..config import add_date as add_date_config
from ..config import get_dates
from ..config import remove_date as remove_date_config
from . import clock


def parse_due_date(due_str: str) -> str | None:
    """Parses a due date string (e.g., 'today', 'tomorrow', 'mon', 'YYYY-MM-DD')."""
    due_str_lower = due_str.lower()
    today = clock.today()

    if due_str_lower == "today":
        return today.isoformat()
    if due_str_lower == "tomorrow":
        return (today + timedelta(days=1)).isoformat()
    if due_str_lower in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
        day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
        current_weekday = today.weekday()  # Monday is 0, Sunday is 6
        target_weekday = day_map[due_str_lower]
        days_ahead = (target_weekday - current_weekday + 7) % 7
        if days_ahead == 0 and due_str_lower != today.strftime("%a").lower():
            days_ahead = 7  # If today is the target day, but we mean next week
        return (today + timedelta(days=days_ahead)).isoformat()
    try:
        # Attempt to parse as YYYY-MM-DD
        parsed_date = date.fromisoformat(due_str)
        return parsed_date.isoformat()
    except ValueError:
        return None  # Invalid date format


def list_dates() -> list[dict[str, str]]:
    """Get all dates, sorted by date."""
    dates = get_dates()
    return sorted(dates, key=lambda x: x["date"])


def add_date(name: str, date_str: str, emoji: str) -> None:
    """Add a date to config."""
    add_date_config(name, date_str, emoji)


def remove_date(name: str) -> None:
    """Remove a date from config."""
    remove_date_config(name)
