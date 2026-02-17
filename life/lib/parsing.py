import re

from .dates import parse_due_date


def validate_content(content: str) -> None:
    """Validate that content is not empty or whitespace-only.

    Raises ValueError if invalid.
    """
    if not content or not content.strip():
        raise ValueError("Content cannot be empty or whitespace-only")


def parse_due_and_item(args: list[str], remove: bool = False) -> tuple[str | None, str]:
    """Parse due date and item name from variadic args.

    Returns (date_str, item_name) tuple.
    Raises ValueError if parsing fails.
    """
    if not args:
        raise ValueError("Due date and item required")

    date_str = None
    item_args = args

    if not remove and len(args) > 0:
        parsed = parse_due_date(args[0])
        if parsed:
            date_str = parsed
            item_args = args[1:]

    if not item_args:
        raise ValueError("Item name required")

    item_name = " ".join(item_args)
    return date_str, item_name


def parse_time(time_str: str) -> str:
    time_str = time_str.strip().lower()
    m = re.match(r"^(\d{1,2}):(\d{2})$", time_str)
    if m:
        h, mn = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mn <= 59:
            return f"{h:02d}:{mn:02d}"
    raise ValueError(f"Invalid time '{time_str}' — use HH:MM")
