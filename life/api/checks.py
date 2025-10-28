import contextlib
import sqlite3

from .. import db
from ..lib import clock
from ..lib.converters import _row_to_item
from . import items
from .models import Item


def add_check(item_id, check_date=None):
    """Add a check for a habit."""
    item = items.get_item(item_id)
    if not item or not item.is_habit:
        raise ValueError("Checks can only be added to habits.")

    check_date_str = check_date or clock.today().isoformat()

    with db.get_db() as conn:
        with contextlib.suppress(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO checks (item_id, check_date) VALUES (?, ?)",
                (item_id, check_date_str),
            )


def delete_check(item_id, check_date=None):
    """Delete a check for a habit."""
    check_date_str = check_date or clock.today().isoformat()
    with db.get_db() as conn:
        conn.execute(
            "DELETE FROM checks WHERE item_id = ? AND check_date = ?",
            (item_id, check_date_str),
        )


def get_checked_habits_today() -> list[Item]:
    today_str = clock.today().isoformat()
    with db.get_db() as conn:
        cursor = conn.execute(
            """
            SELECT i.id, i.content, i.focus, i.due_date, i.created, i.completed, i.is_habit
            FROM items i
            INNER JOIN checks c ON i.id = c.item_id
            WHERE date(c.check_date) = ? AND i.is_habit = 1
            """,
            (today_str,),
        )
        return [_row_to_item(row) for row in cursor.fetchall()]


def count_today() -> int:
    today_str = clock.today().isoformat()
    with db.get_db() as conn:
        cursor = conn.execute(
            """
            SELECT COUNT(c.item_id)
            FROM checks c
            INNER JOIN items i ON c.item_id = i.id
            WHERE date(c.check_date) = ? AND i.is_habit = 1
            """,
            (today_str,),
        )
        result = cursor.fetchone()
        return result[0] if result else 0


def get_checks(item_id: str) -> list[str]:
    """Get all check dates for a given item."""
    with db.get_db() as conn:
        cursor = conn.execute("SELECT check_date FROM checks WHERE item_id = ?", (item_id,))
        return [row[0] for row in cursor.fetchall()]
