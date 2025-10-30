import dataclasses
from datetime import date, datetime

from ..api.models import Habit, Task


def _parse_date(val) -> date | None:
    """Parse a date value that may be str or numeric timestamp."""
    if isinstance(val, str) and val:
        return date.fromisoformat(val.split("T")[0])
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val).date()
    return None


def _parse_datetime(val) -> datetime:
    """Parse a datetime value that may be str or numeric timestamp."""
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val)
    if isinstance(val, str) and val:
        try:
            return datetime.fromisoformat(val)
        except ValueError:
            return datetime.combine(date.fromisoformat(val), datetime.min.time())
    return datetime.min


def _parse_datetime_optional(val) -> datetime | None:
    """Parse an optional datetime value that may be str or numeric timestamp."""
    if isinstance(val, str) and val:
        try:
            return datetime.fromisoformat(val)
        except ValueError:
            return datetime.combine(date.fromisoformat(val), datetime.min.time())
    elif isinstance(val, (int, float)):
        return datetime.fromtimestamp(val)
    return None


def _row_to_task(row: tuple) -> Task:
    """
    Converts a raw database row from tasks table into a Task object.
    Expected row format: (id, content, focus, due_date, created, completed)
    """
    return Task(
        id=row[0],
        content=row[1],
        focus=bool(row[2]),
        due_date=_parse_date(row[3]),
        created=_parse_datetime(row[4]),
        completed=_parse_datetime_optional(row[5]),
    )


def _row_to_habit(row: tuple) -> Habit:
    """
    Converts a raw database row from habits table into a Habit object.
    Expected row format: (id, content, created)
    """
    return Habit(
        id=row[0],
        content=row[1],
        created=_parse_datetime(row[2]),
    )


def _hydrate_tags(item: Task | Habit, tags: list[str]) -> Task | Habit:
    """
    Attaches tags list to a Task or Habit object.
    Returns a new frozen dataclass instance with tags populated.
    """
    return dataclasses.replace(item, tags=tags)
