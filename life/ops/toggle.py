from ..api.checks import add_check, delete_check
from ..api.items import get_item, update_item
from ..lib import clock
from .fuzzy import find_item


def toggle_focus(item_id: str, current_focus: bool) -> tuple[str, str]:
    """Toggles the focus status of an item."""
    new_focus = not current_focus
    update_item(item_id, focus=new_focus)
    status_text = "Focused" if new_focus else "Unfocused"
    item = get_item(item_id)
    return status_text, item.content if item else ""


def toggle_done(
    partial: str, date: str | None = None, undo: bool = False
) -> tuple[str, str] | None:
    """Toggle completion status on item (fuzzy match)."""
    item = find_item(partial)
    if not item:
        return None

    if item.is_habit:
        if undo:
            delete_check(item.id, clock.today().isoformat())
        else:
            add_check(item.id, clock.today().isoformat())
    else:
        if undo:
            from .. import db

            with db.get_db() as conn:
                conn.execute("UPDATE items SET completed = NULL WHERE id = ?", (item.id,))
        else:
            update_item(item.id, completed=clock.today().isoformat())

    return item.content, "undone" if undo else "done"
