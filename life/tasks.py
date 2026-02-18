import sqlite3
import uuid
from datetime import datetime

from . import db
from .lib import clock
from .lib.converters import row_to_task
from .lib.fuzzy import find_in_pool
from .models import Task, TaskMutation
from .tags import add_tag, hydrate_tags, load_tags_for_tasks

__all__ = [
    "add_task",
    "defer_task",
    "delete_task",
    "find_task",
    "find_task_any",
    "get_all_tasks",
    "get_focus",
    "get_mutations",
    "get_task",
    "get_tasks",
    "set_blocked_by",
    "toggle_completed",
    "toggle_focus",
    "update_task",
]


def _task_sort_key(task: Task) -> tuple[bool, bool, object, object]:
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
            "SELECT id, content, focus, due_date, created, completed_at, parent_id, due_time, blocked_by FROM tasks WHERE id = ?",
            (task_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        task = row_to_task(row)
        tags_map = load_tags_for_tasks([task_id], conn=conn)
        return hydrate_tags([task], tags_map)[0]


def get_tasks() -> list[Task]:
    """SELECT pending (incomplete) tasks, sorted by (focus DESC, due_date ASC, created ASC)."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due_date, created, completed_at, parent_id, due_time, blocked_by FROM tasks WHERE completed_at IS NULL"
        )
        tasks = [row_to_task(row) for row in cursor.fetchall()]
        task_ids = [t.id for t in tasks]
        tags_map = load_tags_for_tasks(task_ids, conn=conn)
        result = hydrate_tags(tasks, tags_map)

    return sorted(result, key=_task_sort_key)


def get_all_tasks() -> list[Task]:
    """SELECT all tasks (including completed), sorted by canonical key."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due_date, created, completed_at, parent_id, due_time, blocked_by FROM tasks"
        )
        tasks = [row_to_task(row) for row in cursor.fetchall()]
        task_ids = [t.id for t in tasks]
        tags_map = load_tags_for_tasks(task_ids, conn=conn)
        result = hydrate_tags(tasks, tags_map)

    return sorted(result, key=_task_sort_key)


def get_focus() -> list[Task]:
    """SELECT focus = 1 AND completed_at IS NULL."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due_date, created, completed_at, parent_id, due_time, blocked_by FROM tasks WHERE focus = 1 AND completed_at IS NULL"
        )
        tasks = [row_to_task(row) for row in cursor.fetchall()]
        task_ids = [t.id for t in tasks]
        tags_map = load_tags_for_tasks(task_ids, conn=conn)
        return hydrate_tags(tasks, tags_map)


_TRACKED_FIELDS = {"content", "due_date", "due_time", "focus", "completed_at"}


def _record_mutation(conn: sqlite3.Connection, task_id: str, field: str, old_val, new_val) -> None:
    if field not in _TRACKED_FIELDS:
        return
    old_str = str(old_val) if old_val is not None else None
    new_str = str(new_val) if new_val is not None else None
    if old_str == new_str:
        return
    conn.execute(
        "INSERT INTO task_mutations (task_id, field, old_value, new_value) VALUES (?, ?, ?, ?)",
        (task_id, field, old_str, new_str),
    )


def _record_mutations(
    conn: sqlite3.Connection, task_id: str, old: Task, updates: dict[str, str]
) -> None:
    for field, new_val in updates.items():
        _record_mutation(conn, task_id, field, getattr(old, field, None), new_val)


_UNSET = object()


def update_task(
    task_id: str,
    content: str | None = None,
    focus: bool | None = None,
    due: str | object = _UNSET,
    due_time: str | object = _UNSET,
) -> Task | None:
    """Partial update, return updated Task. Pass None to clear a nullable field."""
    updates = {}
    if content is not None:
        updates["content"] = content
    if focus is not None:
        updates["focus"] = focus
    if due is not _UNSET:
        updates["due_date"] = due
    if due_time is not _UNSET:
        updates["due_time"] = due_time

    if updates:
        old = get_task(task_id)
        set_clauses = [f"{k} = ?" for k in updates]
        values = list(updates.values())
        values.append(task_id)

        with db.get_db() as conn:
            try:
                conn.execute(
                    f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?",  # noqa: S608
                    tuple(values),
                )
                if old:
                    _record_mutations(conn, task_id, old, updates)
            except sqlite3.IntegrityError as e:
                raise ValueError(f"Failed to update task: {e}") from e

    return get_task(task_id)


def get_mutations(task_id: str) -> list[TaskMutation]:
    """Return all recorded mutations for a task, newest first."""
    with db.get_db() as conn:
        rows = conn.execute(
            "SELECT id, task_id, field, old_value, new_value, mutated_at, reason FROM task_mutations WHERE task_id = ? ORDER BY mutated_at DESC",
            (task_id,),
        ).fetchall()

    return [
        TaskMutation(
            id=r[0],
            task_id=r[1],
            field=r[2],
            old_value=r[3],
            new_value=r[4],
            mutated_at=datetime.fromisoformat(r[5]),
            reason=r[6],
        )
        for r in rows
    ]


def defer_task(task_id: str, reason: str) -> Task | None:
    """Record an explicit deferral with reason. Does not reschedule."""
    task = get_task(task_id)
    if not task:
        return None
    with db.get_db() as conn:
        conn.execute(
            "INSERT INTO task_mutations (task_id, field, old_value, new_value, reason) VALUES (?, 'defer', NULL, NULL, ?)",
            (task_id, reason),
        )
    return task


def delete_task(task_id: str) -> None:
    """DELETE from tasks."""
    with db.get_db() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def toggle_completed(task_id: str) -> Task | None:
    """Toggle task completion. If completed, mark as pending. If pending, mark as complete."""
    task = get_task(task_id)
    if not task:
        return None

    if task.completed_at:
        with db.get_db() as conn:
            conn.execute("UPDATE tasks SET completed_at = NULL WHERE id = ?", (task_id,))
            _record_mutation(conn, task_id, "completed_at", task.completed_at, None)
    else:
        completed = clock.now().strftime("%Y-%m-%dT%H:%M:%S")
        with db.get_db() as conn:
            conn.execute(
                "UPDATE tasks SET completed_at = ? WHERE id = ?",
                (completed, task_id),
            )
            _record_mutation(conn, task_id, "completed_at", None, completed)
            conn.execute(
                "UPDATE tasks SET blocked_by = NULL WHERE blocked_by = ?",
                (task_id,),
            )

    return get_task(task_id)


def toggle_focus(task_id: str) -> Task | None:
    """Toggle task focus status."""
    task = get_task(task_id)
    if not task:
        return None

    new_focus = not task.focus
    return update_task(task_id, focus=new_focus)


def find_task(ref: str) -> Task | None:
    return find_in_pool(ref, get_tasks())


def find_task_any(ref: str) -> Task | None:
    return find_in_pool(ref, get_all_tasks())


def set_blocked_by(task_id: str, blocker_id: str | None) -> Task | None:
    """Set or clear the blocked_by pointer on a task."""
    with db.get_db() as conn:
        conn.execute(
            "UPDATE tasks SET blocked_by = ? WHERE id = ?",
            (blocker_id, task_id),
        )
    return get_task(task_id)
