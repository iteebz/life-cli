import sqlite3
import uuid
from datetime import date, timedelta

from ..lib.sqlite import DB_PATH, init_db

_CLEAR = object()


def add_item(content, focus=False, due=None, target_count=5, tags=None):
    """Add item to database"""
    init_db()
    item_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO items (id, content, focus, due, target_count) VALUES (?, ?, ?, ?, ?)",
        (item_id, content, focus, due, target_count),
    )

    if tags:
        for tag in tags:
            conn.execute(
                "INSERT INTO item_tags (id, item_id, tag) VALUES (?, ?, ?)",
                (str(uuid.uuid4()), item_id, tag.lower()),
            )

    conn.commit()
    conn.close()
    return item_id


def get_pending_items():
    """Get all pending items ordered by focus and due date"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT i.id, i.content, i.focus, i.due, i.created, MAX(c.checked), COUNT(c.id), i.target_count
        FROM items i
        LEFT JOIN checks c ON i.id = c.item_id
        WHERE i.completed IS NULL
        GROUP BY i.id
        ORDER BY i.focus DESC, i.due IS NULL, i.due ASC, i.created ASC
    """)
    items = cursor.fetchall()
    conn.close()
    return items


def today_completed():
    """Get count of items completed today (both regular and repeats)"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    today_str = date.today().isoformat()

    cursor = conn.execute(
        "SELECT COUNT(*) FROM items WHERE DATE(completed) = ?",
        (today_str,),
    )
    item_count = cursor.fetchone()[0]

    cursor = conn.execute(
        "SELECT COUNT(*) FROM checks WHERE DATE(checked) = ?",
        (today_str,),
    )
    check_count = cursor.fetchone()[0]

    conn.close()
    return item_count + check_count


def weekly_momentum():
    """Get weekly completion stats for this week and last week"""
    init_db()
    conn = sqlite3.connect(DB_PATH)

    today = date.today()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    last_week_start = week_start - timedelta(days=7)
    last_week_end = week_start

    week_start_str = week_start.isoformat()
    last_week_start_str = last_week_start.isoformat()
    last_week_end_str = last_week_end.isoformat()

    cursor = conn.execute(
        "SELECT COUNT(*) FROM items WHERE completed IS NOT NULL AND DATE(completed) >= ?",
        (week_start_str,),
    )
    this_week_items = cursor.fetchone()[0]

    cursor = conn.execute(
        "SELECT COUNT(*) FROM checks WHERE DATE(checked) >= ?",
        (week_start_str,),
    )
    this_week_checks = cursor.fetchone()[0]
    this_week_completed = this_week_items + this_week_checks

    cursor = conn.execute(
        "SELECT COUNT(*) FROM items WHERE DATE(created) >= ?",
        (week_start_str,),
    )
    this_week_added = cursor.fetchone()[0]

    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM items
        WHERE completed IS NOT NULL
        AND DATE(completed) >= ?
        AND DATE(completed) < ?
    """,
        (last_week_start_str, last_week_end_str),
    )
    last_week_items = cursor.fetchone()[0]

    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM checks
        WHERE DATE(checked) >= ?
        AND DATE(checked) < ?
    """,
        (last_week_start_str, last_week_end_str),
    )
    last_week_checks = cursor.fetchone()[0]
    last_week_completed = last_week_items + last_week_checks

    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM items
        WHERE DATE(created) >= ?
        AND DATE(created) < ?
    """,
        (last_week_start_str, last_week_end_str),
    )
    last_week_added = cursor.fetchone()[0]

    conn.close()
    return this_week_completed, this_week_added, last_week_completed, last_week_added


def complete_item(item_id):
    """Mark item as completed"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE items SET completed = CURRENT_TIMESTAMP, focus = 0 WHERE id = ?", (item_id,)
    )
    conn.commit()
    conn.close()


def uncomplete_item(item_id):
    """Mark item as incomplete"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE items SET completed = NULL WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def update_item(item_id, content=None, due=_CLEAR, focus=None):
    """Update item fields"""
    init_db()
    conn = sqlite3.connect(DB_PATH)

    updates = []
    params = []

    if content is not None:
        updates.append("content = ?")
        params.append(content)
    if due is not _CLEAR:
        updates.append("due = ?")
        params.append(due)
    if focus is not None:
        updates.append("focus = ?")
        params.append(1 if focus else 0)

    if updates:
        query = f"UPDATE items SET {', '.join(updates)} WHERE id = ?"
        params.append(item_id)
        conn.execute(query, params)
        conn.commit()

    conn.close()


def toggle_focus(item_id, current_focus):
    """Toggle focus status of item"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    new_focus = 1 if current_focus == 0 else 0
    conn.execute("UPDATE items SET focus = ? WHERE id = ?", (new_focus, item_id))
    conn.commit()
    conn.close()
    return new_focus


def delete_item(item_id):
    """Delete an item from the database"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def get_today_completed():
    """Get all items completed today (both regular and repeats)"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    today_str = date.today().isoformat()

    cursor = conn.execute(
        """
        SELECT id, content, completed
        FROM items
        WHERE DATE(completed) = ?
        ORDER BY completed DESC
    """,
        (today_str,),
    )
    completed_items = cursor.fetchall()

    cursor = conn.execute(
        """
        SELECT i.id, i.content, c.checked
        FROM items i
        INNER JOIN checks c ON i.id = c.item_id
        WHERE DATE(c.checked) = ?
        ORDER BY c.checked DESC
    """,
        (today_str,),
    )
    checked_items = cursor.fetchall()

    conn.close()
    return completed_items + checked_items


def is_repeating(item_id):
    """Check if item is a repeating item (has habit or chore tag)"""
    from .tag import get_tags

    tags = get_tags(item_id)
    return any(tag in ("habit", "chore") for tag in tags)


def add_task(content, focus=False, due=None, done=False, tags=None):
    """Add task, optionally complete immediately. Returns message string."""
    from ..app.render import fmt_add_task

    add_item(content, focus=focus, due=due, tags=tags)
    if done:
        from ..lib.match import complete

        complete(content)
    return fmt_add_task(content, focus=focus, due=due, done=done, tags=tags)


def add_habit(content):
    """Add habit item. Returns message string."""
    from ..app.render import fmt_add_habit

    add_item(content, tags=["habit"])
    return fmt_add_habit(content)


def add_chore(content):
    """Add chore item. Returns message string."""
    from ..app.render import fmt_add_chore

    add_item(content, tags=["chore"])
    return fmt_add_chore(content)


def done_item(partial, undo=False):
    """Complete or undo item. Returns message string."""
    from ..lib.match import complete, find_item, uncomplete
    from .tag import get_tags

    if not partial:
        return "No item specified"

    if undo:
        uncompleted = uncomplete(partial)
        return f"✓ {uncompleted}" if uncompleted else f"No match for: {partial}"

    completed = complete(partial)
    if not completed:
        return f"No match for: {partial}"

    item = find_item(partial)
    if item:
        tags = get_tags(item[0])
        tags_str = " " + " ".join(f"#{t}" for t in tags) if tags else ""
        return f"✓ {completed}{tags_str}"
    return f"✓ {completed}"
