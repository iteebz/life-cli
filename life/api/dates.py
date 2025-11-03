from ..config import add_date as add_date_config
from ..config import get_dates
from ..config import remove_date as remove_date_config


def list_dates() -> list[dict]:
    """Get all dates, sorted by date."""
    dates = get_dates()
    return sorted(dates, key=lambda x: x["date"])


def add_date(name: str, date_str: str, emoji: str) -> None:
    """Add a date to config."""
    add_date_config(name, date_str, emoji)


def remove_date(name: str) -> None:
    """Remove a date from config."""
    remove_date_config(name)
