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
