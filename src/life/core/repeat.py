import sqlite3
from datetime import date

from ..lib.sqlite import DB_PATH, init_db


def check_repeat(item_id, check_date=None):
    """Record a repeat check, one per day max. Skip if already checked today. Auto-complete if target reached."""
    import uuid

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
