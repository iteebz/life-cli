import sqlite3


def migration_023_steward_task_field(conn: sqlite3.Connection) -> None:
    cursor = conn.execute("PRAGMA table_info(tasks)")
    columns = [row[1] for row in cursor.fetchall()]
    if "steward" not in columns:
        conn.execute("ALTER TABLE tasks ADD COLUMN steward BOOLEAN NOT NULL DEFAULT 0")
    conn.execute(
        "UPDATE tasks SET steward = 1 WHERE id IN (SELECT task_id FROM tags WHERE tag = 'steward' AND task_id IS NOT NULL)"
    )


def migration_024_remove_steward_tag(conn: sqlite3.Connection) -> set[str]:
    conn.execute("DELETE FROM tags WHERE tag = 'steward'")
    return {"tags"}
