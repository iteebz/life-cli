import uuid

from .. import db
from ..lib import clock
from ..lib.converters import _hydrate_tags, _row_to_task
from .models import Task
from .tags import add_tag


def add_task(
    content: str, focus: bool = False, due: str | None = None, tags: list[str] | None = None
) -> str:
    """Adds a new task. Returns task_id."""
    task_id = str(uuid.uuid4())
    with db.get_db() as conn:
        conn.execute(
            "INSERT INTO tasks (id, content, focus, due_date, created) VALUES (?, ?, ?, ?, ?)",
            (task_id, content, focus, due, clock.today().isoformat()),
        )
        if tags:
            for tag in tags:
                add_tag(task_id, None, tag)
    return task_id


def get_task(task_id: str) -> Task | None:
    """SELECT from tasks + LEFT JOIN tags, return Task or None."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due_date, created, completed FROM tasks WHERE id = ?",
            (task_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        task = _row_to_task(row)

        cursor = conn.execute("SELECT tag FROM tags WHERE task_id = ?", (task_id,))
        task_tags = [tag_row[0] for tag_row in cursor.fetchall()]

        return _hydrate_tags(task, task_tags)


def get_all_tasks() -> list[Task]:
    """SELECT all tasks with tags."""
    with db.get_db() as conn:
        cursor = conn.execute("SELECT id, content, focus, due_date, created, completed FROM tasks")
        tasks = [_row_to_task(row) for row in cursor.fetchall()]

        result = []
        for task in tasks:
            cursor = conn.execute("SELECT tag FROM tags WHERE task_id = ?", (task.id,))
            task_tags = [tag_row[0] for tag_row in cursor.fetchall()]
            result.append(_hydrate_tags(task, task_tags))

        return result


def get_pending_tasks() -> list[Task]:
    """SELECT completed IS NULL, sorted by (focus DESC, due_date ASC, created ASC)."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due_date, created, completed FROM tasks WHERE completed IS NULL"
        )
        tasks = [_row_to_task(row) for row in cursor.fetchall()]

        result = []
        for task in tasks:
            cursor = conn.execute("SELECT tag FROM tags WHERE task_id = ?", (task.id,))
            task_tags = [tag_row[0] for tag_row in cursor.fetchall()]
            result.append(_hydrate_tags(task, task_tags))

    return sorted(
        result,
        key=lambda task: (
            not task.focus,
            task.due_date is None,
            task.due_date,
            task.created,
        ),
    )


def get_focus_tasks() -> list[Task]:
    """SELECT focus = 1 AND completed IS NULL."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due_date, created, completed FROM tasks WHERE focus = 1 AND completed IS NULL"
        )
        tasks = [_row_to_task(row) for row in cursor.fetchall()]

        result = []
        for task in tasks:
            cursor = conn.execute("SELECT tag FROM tags WHERE task_id = ?", (task.id,))
            task_tags = [tag_row[0] for tag_row in cursor.fetchall()]
            result.append(_hydrate_tags(task, task_tags))

        return result


def complete_task(task_id: str) -> Task:
    """UPDATE completed = now(), return updated Task."""
    with db.get_db() as conn:
        conn.execute(
            "UPDATE tasks SET completed = ? WHERE id = ?",
            (clock.today().isoformat(), task_id),
        )
    return get_task(task_id)


def update_task(
    task_id: str, content: str | None = None, focus: bool | None = None, due: str | None = None
) -> Task:
    """Partial update, return updated Task."""
    updates = {
        "content": content,
        "focus": focus,
        "due_date": due,
    }
    updates = {k: v for k, v in updates.items() if v is not None}

    if updates:
        set_clauses = [f"{k} = ?" for k in updates]
        values = list(updates.values())
        values.append(task_id)

        with db.get_db() as conn:
            conn.execute(f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?", tuple(values))

    return get_task(task_id)


def delete_task(task_id: str) -> None:
    """DELETE from tasks."""
    with db.get_db() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def get_today_completed_tasks() -> list[Task]:
    """SELECT completed tasks from today."""
    today_str = clock.today().isoformat()
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due_date, created, completed FROM tasks WHERE date(completed) = ? AND completed IS NOT NULL",
            (today_str,),
        )
        tasks = [_row_to_task(row) for row in cursor.fetchall()]

        result = []
        for task in tasks:
            cursor = conn.execute("SELECT tag FROM tags WHERE task_id = ?", (task.id,))
            task_tags = [tag_row[0] for tag_row in cursor.fetchall()]
            result.append(_hydrate_tags(task, task_tags))

        return result
