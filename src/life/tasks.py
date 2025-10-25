import sqlite3
import uuid
from datetime import date, timedelta

from .sqlite import DB_PATH, init_db

_CLEAR = object()


def add_task(content, category="task", focus=False, due=None, target_count=5):
    """Add task to database"""
    init_db()
    task_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO tasks (id, content, category, focus, due, target_count) VALUES (?, ?, ?, ?, ?, ?)",
        (task_id, content, category, focus, due, target_count),
    )
    conn.commit()
    conn.close()
    return task_id


def get_pending_tasks():
    """Get all pending tasks ordered by focus and due date"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT t.id, t.content, t.category, t.focus, t.due, t.created, MAX(c.checked), COUNT(c.id), t.target_count
        FROM tasks t
        LEFT JOIN checks c ON t.id = c.reminder_id
        WHERE t.completed IS NULL
        GROUP BY t.id
        ORDER BY t.focus DESC, t.due ASC NULLS LAST, t.created ASC
    """)
    tasks = cursor.fetchall()
    conn.close()
    return tasks


def today_completed():
    """Get count of tasks completed and checks today"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    today_str = date.today().isoformat()

    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE DATE(completed) = ?
    """,
        (today_str,),
    )
    task_count = cursor.fetchone()[0]

    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM checks
        WHERE DATE(checked) = ?
    """,
        (today_str,),
    )
    check_count = cursor.fetchone()[0]

    conn.close()
    return task_count + check_count


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
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE completed IS NOT NULL
        AND DATE(completed) >= ?
    """,
        (week_start_str,),
    )
    this_week_tasks = cursor.fetchone()[0]

    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM checks
        WHERE DATE(checked) >= ?
    """,
        (week_start_str,),
    )
    this_week_checks = cursor.fetchone()[0]
    this_week_completed = this_week_tasks + this_week_checks

    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE DATE(created) >= ?
    """,
        (week_start_str,),
    )
    this_week_added = cursor.fetchone()[0]

    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE completed IS NOT NULL
        AND DATE(completed) >= ?
        AND DATE(completed) < ?
    """,
        (last_week_start_str, last_week_end_str),
    )
    last_week_tasks = cursor.fetchone()[0]

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
    last_week_completed = last_week_tasks + last_week_checks

    cursor = conn.execute(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE DATE(created) >= ?
        AND DATE(created) < ?
    """,
        (last_week_start_str, last_week_end_str),
    )
    last_week_added = cursor.fetchone()[0]

    conn.close()
    return this_week_completed, this_week_added, last_week_completed, last_week_added


def complete_task(task_id):
    """Mark task as completed and unfocus"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE tasks SET completed = CURRENT_TIMESTAMP, focus = 0 WHERE id = ?", (task_id,)
    )
    conn.commit()
    conn.close()


def uncomplete_task(task_id):
    """Mark task as incomplete"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE tasks SET completed = NULL WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def update_task(task_id, content=None, due=_CLEAR, focus=None):
    """Update task fields"""
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
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        params.append(task_id)
        conn.execute(query, params)
        conn.commit()

    conn.close()


def toggle_focus(task_id, current_focus, category=None):
    """Toggle focus status of task (tasks only)"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    if category and category != "task":
        conn.close()
        return current_focus
    new_focus = 1 if current_focus == 0 else 0
    conn.execute("UPDATE tasks SET focus = ? WHERE id = ?", (new_focus, task_id))
    conn.commit()
    conn.close()
    return new_focus


def clear_all_tasks():
    """Delete all tasks"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM tasks")
    conn.commit()
    conn.close()


def delete_task(task_id):
    """Delete a task from the database"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def add_tag(task_id, tag):
    """Add a tag to a task"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO task_tags (task_id, tag) VALUES (?, ?)",
            (task_id, tag.lower()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


def get_tags(task_id):
    """Get all tags for a task"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT tag FROM task_tags WHERE task_id = ?", (task_id,))
    tags = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tags


def get_tasks_by_tag(tag):
    """Get all pending tasks with a specific tag"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        """
        SELECT t.id, t.content, t.category, t.focus, t.due, t.created, MAX(c.checked), COUNT(c.id), t.target_count
        FROM tasks t
        LEFT JOIN checks c ON t.id = c.reminder_id
        INNER JOIN task_tags tt ON t.id = tt.task_id
        WHERE t.completed IS NULL AND tt.tag = ?
        GROUP BY t.id
        ORDER BY t.focus DESC, t.due ASC NULLS LAST, t.created ASC
    """,
        (tag.lower(),),
    )
    tasks = cursor.fetchall()
    conn.close()
    return tasks


def remove_tag(task_id, tag):
    """Remove a tag from a task"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "DELETE FROM task_tags WHERE task_id = ? AND tag = ?",
        (task_id, tag.lower()),
    )
    conn.commit()
    conn.close()


def get_today_completed():
    """Get all tasks completed today and habit/chore checks today"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    today_str = date.today().isoformat()

    cursor = conn.execute(
        """
        SELECT id, content, category, completed
        FROM tasks
        WHERE DATE(completed) = ? AND category = 'task'
        ORDER BY completed DESC
    """,
        (today_str,),
    )
    completed_tasks = cursor.fetchall()

    cursor = conn.execute(
        """
        SELECT t.id, t.content, t.category, c.checked
        FROM tasks t
        INNER JOIN checks c ON t.id = c.reminder_id
        WHERE DATE(c.checked) = ? AND (t.category = 'habit' OR t.category = 'chore')
        ORDER BY c.checked DESC
    """,
        (today_str,),
    )
    checked_items = cursor.fetchall()

    conn.close()
    return completed_tasks + checked_items
