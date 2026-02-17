import sqlite3
import uuid

from . import db
from .lib import clock
from .lib.converters import _row_to_task
from .models import Task
from .tags import add_tag, hydrate_tags, load_tags_for_tasks


def _task_sort_key(task: Task) -> tuple:
    """Canonical sort order: focus first, then by due date, then by creation."""
    return (
        not task.focus,
        task.due_date is None,
        task.due_date,
        task.created,
    )


def add_task(
    content: str,
    focus: bool = False,
    due: str | None = None,
    tags: list[str] | None = None,
    parent_id: str | None = None,
) -> str:
    """Adds a new task. Returns task_id."""
    task_id = str(uuid.uuid4())
    with db.get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO tasks (id, content, focus, due_date, created, parent_id) VALUES (?, ?, ?, ?, ?, ?)",
                (task_id, content, focus, due, clock.today().isoformat(), parent_id),
            )
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to add task: {e}") from e
        if tags:
            for tag in tags:
                add_tag(task_id, None, tag, conn=conn)
    return task_id


def get_task(task_id: str) -> Task | None:
    """SELECT from tasks + LEFT JOIN tags, return Task or None."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due_date, created, completed, parent_id FROM tasks WHERE id = ?",
            (task_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        task = _row_to_task(row)
        tags_map = load_tags_for_tasks([task_id], conn=conn)
        return hydrate_tags([task], tags_map)[0]


def get_tasks() -> list[Task]:
    """SELECT pending (incomplete) tasks, sorted by (focus DESC, due_date ASC, created ASC)."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due_date, created, completed, parent_id FROM tasks WHERE completed IS NULL"
        )
        tasks = [_row_to_task(row) for row in cursor.fetchall()]
        task_ids = [t.id for t in tasks]
        tags_map = load_tags_for_tasks(task_ids, conn=conn)
        result = hydrate_tags(tasks, tags_map)

    return sorted(result, key=_task_sort_key)


def get_all_tasks() -> list[Task]:
    """SELECT all tasks (including completed), sorted by canonical key."""
    with db.get_db() as conn:
        cursor = conn.execute("SELECT id, content, focus, due_date, created, completed, parent_id FROM tasks")
        tasks = [_row_to_task(row) for row in cursor.fetchall()]
        task_ids = [t.id for t in tasks]
        tags_map = load_tags_for_tasks(task_ids, conn=conn)
        result = hydrate_tags(tasks, tags_map)

    return sorted(result, key=_task_sort_key)


def get_focus() -> list[Task]:
    """SELECT focus = 1 AND completed IS NULL."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due_date, created, completed, parent_id FROM tasks WHERE focus = 1 AND completed IS NULL"
        )
        tasks = [_row_to_task(row) for row in cursor.fetchall()]
        task_ids = [t.id for t in tasks]
        tags_map = load_tags_for_tasks(task_ids, conn=conn)
        return hydrate_tags(tasks, tags_map)


def update_task(
    task_id: str, content: str | None = None, focus: bool | None = None, due: str | None = None
) -> Task | None:
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
            try:
                conn.execute(
                    f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?", tuple(values)
                )
            except sqlite3.IntegrityError as e:
                raise ValueError(f"Failed to update task: {e}") from e

    return get_task(task_id)


def delete_task(task_id: str) -> None:
    """DELETE from tasks."""
    with db.get_db() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def toggle_completed(task_id: str) -> Task | None:
    """Toggle task completion. If completed, mark as pending. If pending, mark as complete."""
    task = get_task(task_id)
    if not task:
        return None

    if task.completed:
        with db.get_db() as conn:
            conn.execute("UPDATE tasks SET completed = NULL WHERE id = ?", (task_id,))
    else:
        with db.get_db() as conn:
            conn.execute(
                "UPDATE tasks SET completed = ? WHERE id = ?",
                (clock.today().isoformat(), task_id),
            )

    return get_task(task_id)


def toggle_focus(task_id: str) -> Task | None:
    """Toggle task focus status."""
    task = get_task(task_id)
    if not task:
        return None

    new_focus = not task.focus
    return update_task(task_id, focus=new_focus)
