import contextlib
import sqlite3
from datetime import date, datetime

from .. import db
from .models import Item


def _row_to_item_tag(row) -> Item:
    return Item(
        id=row[0],
        content=row[1],
        focus=bool(row[2]),
        due=date.fromisoformat(row[3]) if isinstance(row[3], str) else None,
        created=datetime.fromtimestamp(row[4])
        if isinstance(row[4], (int, float))
        else datetime.min,
        completed=datetime.fromtimestamp(row[5]) if isinstance(row[5], (int, float)) else None,
        is_repeat=bool(row[6]) if len(row) > 6 else False,
    )


def add_tag(item_id, tag):
    with db.get_db() as conn:
        with contextlib.suppress(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO tags (item_id, tag) VALUES (?, ?)",
                (item_id, tag.lower()),
            )


def get_tags(item_id):
    with db.get_db() as conn:
        cursor = conn.execute("SELECT tag FROM tags WHERE item_id = ?", (item_id,))
        return [row[0] for row in cursor.fetchall()]


def get_items_by_tag(tag):
    with db.get_db() as conn:
        cursor = conn.execute(
            """
            SELECT DISTINCT i.id, i.content, i.focus, i.due, i.created, i.completed, i.is_repeat FROM items i
            INNER JOIN tags it ON i.id = it.item_id
            WHERE it.tag = ?
            """,
            (tag.lower(),),
        )
        return [_row_to_item_tag(row) for row in cursor.fetchall()]


def remove_tag(item_id, tag):
    with db.get_db() as conn:
        conn.execute(
            "DELETE FROM tags WHERE item_id = ? AND tag = ?",
            (item_id, tag.lower()),
        )
