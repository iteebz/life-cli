import contextlib
import sqlite3
from collections import defaultdict

from .. import db
from ..lib.converters import _hydrate_tags, _row_to_habit, _row_to_task
from models import Habit, Task


def add_tag(task_id: str | None, habit_id: str | None, tag: str, conn=None) -> None:
    if (task_id is None and habit_id is None) or (task_id is not None and habit_id is not None):
        raise ValueError("Exactly one of (task_id, habit_id) must be not None")

    if conn is None:
        with db.get_db() as conn:
            with contextlib.suppress(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO tags (task_id, habit_id, tag) VALUES (?, ?, ?)",
                    (task_id, habit_id, tag.lower()),
                )
    else:
        with contextlib.suppress(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO tags (task_id, habit_id, tag) VALUES (?, ?, ?)",
                (task_id, habit_id, tag.lower()),
            )


def get_tags_for_task(task_id: str) -> list[str]:
    with db.get_db() as conn:
        cursor = conn.execute("SELECT tag FROM tags WHERE task_id = ?", (task_id,))
        return [row[0] for row in cursor.fetchall()]


def get_tags_for_habit(habit_id: str) -> list[str]:
    with db.get_db() as conn:
        cursor = conn.execute("SELECT tag FROM tags WHERE habit_id = ?", (habit_id,))
        return [row[0] for row in cursor.fetchall()]


def get_tasks_by_tag(tag: str) -> list[Task]:
    with db.get_db() as conn:
        cursor = conn.execute(
            """
            SELECT DISTINCT t.id, t.content, t.focus, t.due_date, t.created, t.completed
            FROM tasks t
            INNER JOIN tags tg ON t.id = tg.task_id
            WHERE tg.tag = ?
            """,
            (tag.lower(),),
        )
        tasks = [_row_to_task(row) for row in cursor.fetchall()]
        task_ids = [t.id for t in tasks]
        tags_map = load_tags_for_tasks(task_ids, conn=conn)
        return hydrate_tags(tasks, tags_map)


def get_habits_by_tag(tag: str) -> list[Habit]:
    with db.get_db() as conn:
        cursor = conn.execute(
            """
            SELECT DISTINCT h.id, h.content, h.created
            FROM habits h
            INNER JOIN tags tg ON h.id = tg.habit_id
            WHERE tg.tag = ?
            """,
            (tag.lower(),),
        )
        habits = [_row_to_habit(row) for row in cursor.fetchall()]
        habit_ids = [h.id for h in habits]
        tags_map = load_tags_for_habits(habit_ids, conn=conn)
        return hydrate_tags(habits, tags_map)


def remove_tag(task_id: str | None, habit_id: str | None, tag: str) -> None:
    if (task_id is None and habit_id is None) or (task_id is not None and habit_id is not None):
        raise ValueError("Exactly one of (task_id, habit_id) must be not None")

    with db.get_db() as conn:
        conn.execute(
            "DELETE FROM tags WHERE (task_id = ? OR habit_id = ?) AND tag = ?",
            (task_id, habit_id, tag.lower()),
        )


def list_all_tags() -> list[str]:
    with db.get_db() as conn:
        cursor = conn.execute("SELECT DISTINCT tag FROM tags ORDER BY tag ASC")
        return [row[0] for row in cursor.fetchall()]


def load_tags_for_tasks(task_ids: list[str], conn=None) -> dict[str, list[str]]:
    """Batch load all tags for multiple tasks.

    Returns dict mapping task_id -> list of tag strings.
    """
    if not task_ids:
        return {}

    use_context = conn is None
    if use_context:
        ctx = db.get_db()
        conn = ctx.__enter__()

    try:
        placeholders = ",".join("?" * len(task_ids))
        cursor = conn.execute(
            f"SELECT task_id, tag FROM tags WHERE task_id IN ({placeholders}) ORDER BY tag",
            task_ids,
        )
        tags_map = defaultdict(list)
        for task_id, tag in cursor.fetchall():
            tags_map[task_id].append(tag)
        return dict(tags_map)
    finally:
        if use_context:
            ctx.__exit__(None, None, None)


def load_tags_for_habits(habit_ids: list[str], conn=None) -> dict[str, list[str]]:
    """Batch load all tags for multiple habits.

    Returns dict mapping habit_id -> list of tag strings.
    """
    if not habit_ids:
        return {}

    use_context = conn is None
    if use_context:
        ctx = db.get_db()
        conn = ctx.__enter__()

    try:
        placeholders = ",".join("?" * len(habit_ids))
        cursor = conn.execute(
            f"SELECT habit_id, tag FROM tags WHERE habit_id IN ({placeholders}) ORDER BY tag",
            habit_ids,
        )
        tags_map = defaultdict(list)
        for habit_id, tag in cursor.fetchall():
            tags_map[habit_id].append(tag)
        return dict(tags_map)
    finally:
        if use_context:
            ctx.__exit__(None, None, None)


def hydrate_tags(items, tag_map: dict[str, list[str]]):
    """Apply tags to a list of items using a pre-loaded tag map.

    Args:
        items: List of Task or Habit objects
        tag_map: Dict mapping item.id -> list of tags

    Returns list of items with tags hydrated.
    """
    return [_hydrate_tags(item, tag_map.get(item.id, [])) for item in items]
