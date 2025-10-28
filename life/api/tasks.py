import uuid
from datetime import date, datetime

from .. import db
from ..lib import clock
from .models import Item
from .utils import _row_to_item # New import


def add_task(content, focus=False, due=None, tags=None):
    item_id = str(uuid.uuid4())
    with db.get_db() as conn:
        conn.execute(
            "INSERT INTO items (id, content, focus, due, created, is_repeat) VALUES (?, ?, ?, ?, ?, ?)",
            (
                item_id,
                content,
                focus,
                due,
                clock.now().timestamp(),
                False,
            ),  # is_repeat is False for tasks
        )
        if tags:
            for tag_name in tags:
                conn.execute(
                    "INSERT INTO tags (item_id, tag) VALUES (?, ?)",
                    (item_id, tag_name.lower()),
                )
    return item_id


def complete_item(item_id, completed_date: str | None = None):
    with db.get_db() as conn:
        conn.execute(
            "UPDATE items SET completed = ?, focus = 0 WHERE id = ?",
            (
                completed_date if completed_date else clock.today().isoformat(),
                item_id,
            ),
        )


def uncomplete_item(item_id):
    with db.get_db() as conn:
        conn.execute("UPDATE items SET completed = NULL WHERE id = ?", (item_id,))


def update_item(item_id, **kwargs):
    with db.get_db() as conn:
        updates = []
        params = []

        if "content" in kwargs:
            updates.append("content = ?")
            params.append(kwargs["content"])
        if "due" in kwargs:
            updates.append("due = ?")
            params.append(kwargs["due"])
        if "focus" in kwargs:
            updates.append("focus = ?")
            params.append(1 if kwargs["focus"] else 0)

        if updates:
            query = f"UPDATE items SET {', '.join(updates)} WHERE id = ?"
            params.append(item_id)
            conn.execute(query, tuple(params))


def toggle_focus(item_id, current_focus):
    new_focus = 1 if current_focus == 0 else 0
    with db.get_db() as conn:
        conn.execute("UPDATE items SET focus = ? WHERE id = ?", (new_focus, item_id))
    return new_focus
