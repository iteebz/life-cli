import sqlite3
from datetime import date

from .sqlite import DB_PATH, init_db


def check_repeat(repeat_id, check_date=None):
    """Record a repeat check, one per day max. Skip if already checked today. Auto-remove if target reached."""
    init_db()
    conn = sqlite3.connect(DB_PATH)

    if not check_date:
        check_date = date.today().isoformat()

    cursor = conn.execute(
        "SELECT id FROM checks WHERE reminder_id = ? AND DATE(checked) = ?",
        (repeat_id, check_date),
    )
    if cursor.fetchone():
        conn.close()
        return

    conn.execute("INSERT INTO checks (reminder_id, checked) VALUES (?, ?)", (repeat_id, check_date))

    cursor = conn.execute("SELECT target_count FROM tasks WHERE id = ?", (repeat_id,))
    target = cursor.fetchone()

    if target:
        cursor = conn.execute("SELECT COUNT(*) FROM checks WHERE reminder_id = ?", (repeat_id,))
        count = cursor.fetchone()[0]
        target_count = target[0]

        if count >= target_count:
            conn.execute("DELETE FROM tasks WHERE id = ?", (repeat_id,))

    conn.commit()
    conn.close()
