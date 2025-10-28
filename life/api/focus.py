from datetime import date, datetime

from .. import db
from ..lib.match import find_item
from . import items
from .models import Item


def _row_to_item_focus(row) -> Item:
    return Item(
        id=row[0],
        content=row[1],
        focus=bool(row[2]),
        due=date.fromisoformat(row[3]) if isinstance(row[3], str) else None,
        created=datetime.fromtimestamp(row[4])
        if isinstance(row[4], (int, float))
        else datetime.min,
        completed=None,  # Focus items are not completed
        is_repeat=bool(row[7]) if len(row) > 7 else False,
    )


def get_focus_items() -> list[Item]:
    with db.get_db() as conn:
        cursor = conn.execute("""
            SELECT i.id, i.content, i.focus, i.due, i.created, MAX(c.check_date), COUNT(c.item_id), i.is_repeat
            FROM items i
            LEFT JOIN checks c ON i.id = c.item_id
            WHERE i.completed IS NULL AND i.focus = 1
            GROUP BY i.id
            ORDER BY i.due IS NULL, i.due ASC, i.created ASC
        """)
        return [_row_to_item_focus(row) for row in cursor.fetchall()]


def is_task_like(item_id: str) -> bool:
    return not items.is_repeating(item_id)


def toggle_focus(partial: str) -> tuple[str, str] | None:
    item = find_item(partial)
    if item and is_task_like(item.id):
        new_focus = items.toggle_focus(item.id, item.focus)
        status = "Focused" if new_focus else "Unfocused"
        return status, item.content
    return None
