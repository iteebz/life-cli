from ..api.items import add_item
from ..api.models import Item


def add_task(
    content: str, focus: bool = False, due_date: str | None = None, tags: list[str] | None = None
) -> Item:
    """Adds a new task."""
    return add_item(content, focus=focus, due_date=due_date, is_habit=False, tags=tags)
