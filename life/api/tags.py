import contextlib
import sqlite3

from .. import db
from ..lib.converters import _row_to_item


def add_tag(item_id, tag, conn=None):
    if conn is None:
        with db.get_db() as conn:
            with contextlib.suppress(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO tags (item_id, tag) VALUES (?, ?)",
                    (item_id, tag.lower()),
                )
    else:
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
            SELECT DISTINCT i.id, i.content, i.focus, i.due_date, i.created, i.completed, i.is_habit FROM items i
            INNER JOIN tags it ON i.id = it.item_id
            WHERE it.tag = ?
            """,
            (tag.lower(),),
        )
        return [_row_to_item(row) for row in cursor.fetchall()]


def remove_tag(item_id, tag):
    with db.get_db() as conn:
        conn.execute(
            "DELETE FROM tags WHERE item_id = ? AND tag = ?",
            (item_id, tag.lower()),
        )
