import uuid
from datetime import date, datetime

from .. import db
from ..lib import clock
from .models import Item


def _row_to_item(row) -> Item:
    return Item(
        id=row[0],
        content=row[1],
        focus=bool(row[2]),
        due=date.fromisoformat(row[3]) if isinstance(row[3], str) else None,
        created=datetime.fromtimestamp(row[4])
        if isinstance(row[4], (int, float))
        else datetime.min,  # Handle INTEGER timestamp
        completed=date.fromisoformat(row[5])
        if isinstance(row[5], str) and row[5]
        else None,  # Handle DATE string
        is_repeat=bool(row[6]) if len(row) > 6 else False,
    )


def add_item(content, focus=False, due=None, is_repeat=None, tags=None):
    if tags and any(t in ("habit", "chore") for t in tags):
        existing = _get_item_by_content(content, tags)
        if existing:
            raise ValueError(f"Duplicate {tags[0]}: {content}")
    auto_repeat = bool(tags and any(t in ("habit", "chore") for t in tags))
    repeat_flag = auto_repeat if is_repeat is None else bool(is_repeat)
    item_id = str(uuid.uuid4())
    with db.get_db() as conn:
        conn.execute(
            "INSERT INTO items (id, content, focus, due, created, is_repeat) VALUES (?, ?, ?, ?, ?, ?)",
            (item_id, content, focus, due, clock.now().timestamp(), repeat_flag),
        )
        if tags:
            for tag_name in tags:
                conn.execute(
                    "INSERT INTO tags (item_id, tag) VALUES (?, ?)",
                    (item_id, tag_name.lower()),
                )
    return item_id


def is_repeating(item_id: str) -> bool:
    """Check if item is flagged as repeating via canonical schema."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT COALESCE(is_repeat, 0) FROM items WHERE id = ?",
            (item_id,),
        )
        row = cursor.fetchone()
    return bool(row[0]) if row else False


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


def delete_item(item_id):
    with db.get_db() as conn:
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))


def toggle_focus(item_id, current_focus):
    new_focus = 1 if current_focus == 0 else 0
    with db.get_db() as conn:
        conn.execute("UPDATE items SET focus = ? WHERE id = ?", (new_focus, item_id))
    return new_focus


def _get_item_by_content(content, tags) -> Item | None:
    tag_filter = tags[0] if tags else None
    if not tag_filter:
        return None

    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT i.id, i.content, i.focus, i.due, i.created, i.completed, i.is_repeat FROM items i INNER JOIN tags t ON i.id = t.item_id WHERE i.content = ? AND t.tag = ? AND i.completed IS NULL",
            (content, tag_filter),
        )
        row = cursor.fetchone()
        if row:
            return _row_to_item(row)
    return None


def get_item_by_id(item_id) -> Item | None:
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due, created, completed, is_repeat FROM items WHERE id = ?",
            (item_id,),
        )
        row = cursor.fetchone()
        if row:
            return _row_to_item(row)
    return None
