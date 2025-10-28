from datetime import date, datetime

from .. import db
from ..lib import clock
from .models import Item
from .tag import get_tags
from .tasks import add_task
from .habits import add_habit
from .utils import _row_to_item


def add_item(content, item_type="task", focus=False, due=None, tags=None):
    if item_type == "habit":
        return add_habit(content, focus=focus, due=due, tags=tags)
    if item_type == "task":
        return add_task(content, focus=focus, due=due, tags=tags)
    raise ValueError(f"Unknown item type: {item_type}. Must be 'task' or 'habit'.")


def delete_item(item_id):
    with db.get_db() as conn:
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))


def toggle_focus(item_id, current_focus):
    new_focus = 1 if current_focus == 0 else 0
    with db.get_db() as conn:
        conn.execute("UPDATE items SET focus = ? WHERE id = ?", (new_focus, item_id))
    return new_focus





def get_item(item_id) -> Item | None:
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due, created, completed, is_repeat FROM items WHERE id = ?",
            (item_id,),
        )
        row = cursor.fetchone()
        if row:
            return _row_to_item(row)
    return None
