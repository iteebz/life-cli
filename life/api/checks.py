import contextlib
import sqlite3

from .. import db
from ..lib import clock


def add_check(item_id, check_date=None):
    """Add a check for a repeating item."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT COALESCE(is_repeat, 0), completed FROM items WHERE id = ?",
            (item_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"Unknown item: {item_id}")
        is_repeat, completed_status = row
        if not is_repeat:
            raise ValueError("Checks can only be added to repeating items.")

        if completed_status is not None:
            raise ValueError("Repeating items cannot be marked as completed.")

        local_today_date_str = check_date or clock.today().isoformat()

        with contextlib.suppress(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO checks (item_id, check_date) VALUES (?, ?)",
                (item_id, local_today_date_str),  # Insert date string
            )


def delete_check(item_id, check_date=None):
    """Delete a check for a repeating item."""
    with db.get_db() as conn:
        local_today_date_str = check_date or clock.today().isoformat()

        conn.execute(
            "DELETE FROM checks WHERE item_id = ? AND check_date = ?",  # Compare with date string
            (item_id, local_today_date_str),
        )


def get_checks(item_id: str) -> list[str]:
    """Get all check dates for a given item."""
    with db.get_db() as conn:
        cursor = conn.execute("SELECT check_date FROM checks WHERE item_id = ?", (item_id,))
        return [row[0] for row in cursor.fetchall()]
