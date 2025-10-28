import datetime

from .. import db
from ..lib import clock
from .models import Item


def _row_to_item_pending(row) -> Item:
    return Item(
        id=row[0],
        content=row[1],
        focus=bool(row[2]),
        due=datetime.date.fromisoformat(row[3]) if isinstance(row[3], str) and row[3] else None,
        created=datetime.datetime.fromtimestamp(row[4])
        if isinstance(row[4], (int, float))
        else datetime.datetime.min,
        completed=None,  # Pending items are not completed
        is_repeat=bool(row[7]) if len(row) > 7 else False,
    )


def _row_to_item_completed(row) -> Item:
    # For get_today_completed (items): id, content, completed
    return Item(
        id=row[0],
        content=row[1],
        focus=False,  # Not relevant for completed items in this context
        due=None,
        created=datetime.datetime.min,  # Placeholder
        completed=datetime.date.fromisoformat(row[2])
        if isinstance(row[2], str) and row[2]
        else None,
        is_repeat=False,
    )


def _row_to_item_checked(row) -> Item:
    # For get_today_completed (checks): i.id, i.content, c.check_date
    return Item(
        id=row[0],
        content=row[1],
        focus=False,
        due=None,
        created=datetime.datetime.min,  # Placeholder, as created is not in the query
        completed=datetime.date.fromisoformat(row[2]),  # row[2] is check_date
        is_repeat=True,  # Checked items are always repeats
    )


def get_pending_items(asc=True) -> list[Item]:
    order = "ASC" if asc else "DESC"
    with db.get_db() as conn:
        cursor = conn.execute(f"""
            SELECT i.id, i.content, i.focus, i.due, i.created, MAX(c.check_date), COUNT(c.item_id), i.is_repeat
            FROM items i
            LEFT JOIN checks c ON i.id = c.item_id
            WHERE i.completed IS NULL
            GROUP BY i.id
            ORDER BY i.focus DESC, i.due IS NULL, i.due ASC, i.created {order}
        """)
        return [_row_to_item_pending(row) for row in cursor.fetchall()]


def get_today_completed() -> list[Item]:
    today_str = clock.today().isoformat()

    with db.get_db() as conn:
        cursor = conn.execute(
            """
            SELECT id, content, completed
            FROM items
            WHERE completed = ?
            ORDER BY completed DESC
        """,
            (today_str,),
        )
        completed_items = [_row_to_item_completed(row) for row in cursor.fetchall()]

        cursor = conn.execute(
            """
            SELECT i.id, i.content, c.check_date
            FROM items i
            INNER JOIN checks c ON i.id = c.item_id
            WHERE c.check_date = ?
            ORDER BY c.check_date DESC
        """,
            (today_str,),
        )
        checked_items = [_row_to_item_checked(row) for row in cursor.fetchall()]

    return completed_items + checked_items


def get_today_breakdown():
    today_str = clock.today().isoformat()

    with db.get_db() as conn:
        cursor = conn.execute(
            """
            SELECT COUNT(*)
            FROM checks c
            INNER JOIN tags it ON c.item_id = it.item_id
            WHERE it.tag = 'habit'
            AND c.check_date = ?
        """,
            (today_str,),
        )
        habits_today = cursor.fetchone()[0]

        cursor = conn.execute(
            """
            SELECT COUNT(*)
            FROM items
            WHERE completed = ?
            AND COALESCE(is_repeat, 0) = 0
        """,
            (today_str,),
        )
        tasks_today = cursor.fetchone()[0]

        cursor = conn.execute(
            """
            SELECT COUNT(*)
            FROM checks c
            INNER JOIN tags it ON c.item_id = it.item_id
            WHERE it.tag = 'chore'
            AND c.check_date = ?
        """,
            (today_str,),
        )
        chores_today = cursor.fetchone()[0]

    return habits_today, tasks_today, chores_today
