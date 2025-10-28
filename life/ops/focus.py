from ..api import items
from ..ops import fuzzy


def toggle(partial: str) -> tuple[str, str] | None:
    item = fuzzy.find_item(partial)
    if item:
        new_focus = not item.focus
        try:
            items.update_item(item.id, focus=new_focus)
            status = "focused" if new_focus else "unfocused"
            return item.content, status
        except Exception as e:
            # The CHECK constraint in the DB will raise an error if we try to focus a habit.
            # We catch it here to provide a friendly message.
            if "CHECK constraint failed" in str(e):
                return item.content, "cannot be focused because it is a habit."
            # Re-raise other exceptions
            raise e
    return None
