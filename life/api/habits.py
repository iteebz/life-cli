import uuid
from datetime import date, datetime

from .. import db
from ..lib import clock
from .models import Item
from .tag import get_tags # Needed for filtering chores
from .utils import _row_to_item, _get_item_by_content # New import


def get_habits() -> list[Item]:
    """Get all items that are considered habits for display (repeating and not tagged as chore)."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due, created, completed, is_repeat FROM items WHERE is_repeat = 1"
        )
        all_repeating_items = [_row_to_item(row) for row in cursor.fetchall()]

    habits_for_display = []
    for item in all_repeating_items:
        tags = get_tags(item.id)
        if "chore" not in tags:
            habits_for_display.append(item)
    return habits_for_display


def is_habit(item_id: str) -> bool:
    """Check if item is flagged as a habit (repeating)."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT COALESCE(is_repeat, 0) FROM items WHERE id = ?",
            (item_id,),
        )
        row = cursor.fetchone()
    return bool(row[0]) if row else False


def add_habit(content, focus=False, due=None, tags=None):


    if tags and any(t in ("habit", "chore") for t in tags):


        existing = _get_item_by_content(content, tags)


        if existing:


            raise ValueError(f"Duplicate {tags[0]}: {content}")

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
                True,
            ),  # is_repeat is True for habits
        )
        if tags:
            for tag_name in tags:
                conn.execute(
                    "INSERT INTO tags (item_id, tag) VALUES (?, ?)",
                    (item_id, tag_name.lower()),
                )
    return item_id
