import sqlite3
import uuid
from datetime import date, timedelta

from .sqlite import DB_PATH, init_db


def add_item(content, focus=False, due=None, target_count=5, tags=None):
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


def get_pending_items(asc=True):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    order = "ASC" if asc else "DESC"
    cursor = conn.execute(f"""
        SELECT i.id, i.content, i.focus, i.due, i.created, MAX(c.checked), COUNT(c.id), i.target_count
        FROM items i
        LEFT JOIN checks c ON i.id = c.item_id
        WHERE i.completed IS NULL
        GROUP BY i.id
        ORDER BY i.focus DESC, i.due IS NULL, i.due ASC, i.created {order}
    """)
    items = cursor.fetchall()
    conn.close()
    return items


def get_today_completed():
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


def get_weekly_momentum():
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
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE items SET completed = CURRENT_TIMESTAMP, focus = 0 WHERE id = ?", (item_id,)
    )
    conn.commit()
    conn.close()


def uncomplete_item(item_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE items SET completed = NULL WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


_CLEAR = object()


def update_item(item_id, content=None, due=_CLEAR, focus=None):
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
    init_db()
    conn = sqlite3.connect(DB_PATH)
    new_focus = 1 if current_focus == 0 else 0
    conn.execute("UPDATE items SET focus = ? WHERE id = ?", (new_focus, item_id))
    conn.commit()
    conn.close()
    return new_focus


def delete_item(item_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def get_completed_today():
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


def add_tag(item_id, tag):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO item_tags (id, item_id, tag) VALUES (?, ?, ?)",
            (str(uuid.uuid4()), item_id, tag.lower()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


def get_tags(item_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT tag FROM item_tags WHERE item_id = ?", (item_id,))
    tags = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tags


def get_items_by_tag(tag):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        """
        SELECT i.id, i.content, i.focus, i.due, i.created, MAX(c.checked), COUNT(c.id), i.target_count
        FROM items i
        LEFT JOIN checks c ON i.id = c.item_id
        INNER JOIN item_tags it ON i.id = it.item_id
        WHERE i.completed IS NULL AND it.tag = ?
        GROUP BY i.id
        ORDER BY i.focus DESC, i.due ASC NULLS LAST, i.created ASC
    """,
        (tag.lower(),),
    )
    items = cursor.fetchall()
    conn.close()
    return items


def remove_tag(item_id, tag):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "DELETE FROM item_tags WHERE item_id = ? AND tag = ?",
        (item_id, tag.lower()),
    )
    conn.commit()
    conn.close()


def check_repeat(item_id, check_date=None):
    init_db()
    conn = sqlite3.connect(DB_PATH)

    if not check_date:
        check_date = date.today().isoformat()

    cursor = conn.execute(
        "SELECT id FROM checks WHERE item_id = ? AND DATE(checked) = ?",
        (item_id, check_date),
    )
    if cursor.fetchone():
        conn.close()
        return

    conn.execute(
        "INSERT INTO checks (id, item_id, checked) VALUES (?, ?, ?)",
        (str(uuid.uuid4()), item_id, check_date),
    )

    cursor = conn.execute("SELECT target_count FROM items WHERE id = ?", (item_id,))
    target = cursor.fetchone()

    if target:
        cursor = conn.execute("SELECT COUNT(*) FROM checks WHERE item_id = ?", (item_id,))
        count = cursor.fetchone()[0]
        target_count = target[0]

        if count >= target_count:
            conn.execute("UPDATE items SET completed = CURRENT_TIMESTAMP WHERE id = ?", (item_id,))

    conn.commit()
    conn.close()


def get_item_by_id(item_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    conn.close()
    return item
