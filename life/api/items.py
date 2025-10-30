import uuid

from .. import db
from ..lib import clock
from ..lib.converters import _row_to_item
from .models import Item
from .tags import add_tag


def get_item(item_id) -> Item | None:
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due_date, created, completed, is_habit FROM items WHERE id = ?",
            (item_id,),
        )
        row = cursor.fetchone()
        if row:
            return _row_to_item(row)
    return None


def add_item(
    content: str,
    focus: bool = False,
    due: str | None = None,
    is_habit: bool = False,
    tags: list[str] | None = None,
    item_type: str | None = None,
    is_repeat: bool | None = None,
) -> str:
    if item_type:
        is_habit = item_type in ("habit", "chore")
    elif is_repeat is not None:
        is_habit = is_repeat

    item_id = str(uuid.uuid4())
    with db.get_db() as conn:
        conn.execute(
            "INSERT INTO items (id, content, focus, due_date, created, is_habit) VALUES (?, ?, ?, ?, ?, ?)",
            (item_id, content, focus, due, clock.today().isoformat(), is_habit),
        )
        if tags:
            for tag in tags:
                add_tag(item_id, tag, conn)
        return item_id


def get_all_items() -> list[Item]:
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due_date, created, completed, is_habit FROM items"
        )
        return [_row_to_item(row) for row in cursor.fetchall()]


def get_pending_items() -> list[Item]:
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due_date, created, completed, is_habit FROM items WHERE completed IS NULL"
        )
        items_list = [_row_to_item(row) for row in cursor.fetchall()]

    return sorted(
        items_list,
        key=lambda item: (
            not item.focus,
            item.due_date is None,
            item.due_date,
            item.created,
        ),
    )


def get_focus_items() -> list[Item]:
    with db.get_db() as conn:
        cursor = conn.execute("""
            SELECT i.id, i.content, i.focus, i.due_date, i.created, MAX(c.check_date), COUNT(c.item_id), i.is_habit
            FROM items i
            LEFT JOIN checks c ON i.id = c.item_id
            WHERE i.completed IS NULL AND i.focus = 1
            GROUP BY i.id
            ORDER BY i.due_date IS NULL, i.due_date ASC, i.created ASC
        """)
        return [_row_to_item(row) for row in cursor.fetchall()]


def update_item(
    item_id: str,
    content: str | None = None,
    completed: str | None = None,
    focus: int | None = None,
    due: str | None = None,
    is_habit: bool | None = None,
) -> Item:
    updates = {
        "content": content,
        "completed": completed,
        "focus": focus,
        "due_date": due,
        "is_habit": is_habit,
    }
    updates = {k: v for k, v in updates.items() if v is not None}

    if not updates:
        return get_item(item_id)

    set_clauses = [f"{k} = ?" for k in updates]
    values = list(updates.values())
    values.append(item_id)

    with db.get_db() as conn:
        conn.execute(f"UPDATE items SET {', '.join(set_clauses)} WHERE id = ?", tuple(values))
        return get_item(item_id)


def get_today_completed() -> list[Item]:
    today_str = clock.today().isoformat()
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due_date, created, completed, is_habit FROM items WHERE date(completed) = ? AND is_habit = 0",
            (today_str,),
        )
        return [_row_to_item(row) for row in cursor.fetchall()]


def get_completed_tasks_today() -> list[Item]:
    return get_today_completed()


def count_completed_tasks_today() -> int:
    today_str = clock.today().isoformat()
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM items WHERE date(completed) = ? AND is_habit = 0", (today_str,)
        )
        return cursor.fetchone()[0]


def delete_item(item_id: str) -> None:
    with db.get_db() as conn:
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))


def complete_item(item_id: str) -> Item:
    return update_item(item_id, completed=clock.today().isoformat())
