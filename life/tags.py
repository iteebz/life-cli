import sqlite3
from collections import defaultdict
from typing import TypeVar

from . import db
from .lib.converters import hydrate_tags_onto, row_to_habit, row_to_task
from .models import Habit, Task

T = TypeVar("T", Task, Habit)

__all__ = [
    "add_tag",
    "get_habits_by_tag",
    "get_tags_for_habit",
    "get_tags_for_task",
    "get_tasks_by_tag",
    "hydrate_tags",
    "list_all_tags",
    "load_tags_for_habits",
    "load_tags_for_tasks",
    "remove_tag",
]


def add_tag(task_id: str | None, habit_id: str | None, tag: str, conn=None) -> None:
    if (task_id is None and habit_id is None) or (task_id is not None and habit_id is not None):
        raise ValueError("Exactly one of (task_id, habit_id) must be not None")

    if conn is None:
        with db.get_db() as conn:
            conn.execute(
                "INSERT INTO tags (task_id, habit_id, tag) VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
                (task_id, habit_id, tag.lower()),
            )
    else:
        conn.execute(
            "INSERT INTO tags (task_id, habit_id, tag) VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
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
            SELECT DISTINCT t.id, t.content, t.focus, t.due_date, t.created, t.completed_at
            FROM tasks t
            INNER JOIN tags tg ON t.id = tg.task_id
            WHERE tg.tag = ?
            """,
            (tag.lower(),),
        )
        tasks = [row_to_task(row) for row in cursor.fetchall()]
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
        habits = [row_to_habit(row) for row in cursor.fetchall()]
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


def load_tags_for_tasks(
    task_ids: list[str], conn: sqlite3.Connection | None = None
) -> dict[str, list[str]]:
    """Batch load all tags for multiple tasks.

    Returns dict mapping task_id -> list of tag strings.
    """
    if not task_ids:
        return {}

    placeholders = ",".join("?" * len(task_ids))
    query = f"SELECT task_id, tag FROM tags WHERE task_id IN ({placeholders}) ORDER BY tag"  # noqa: S608

    def _run(c: sqlite3.Connection) -> dict[str, list[str]]:
        cursor = c.execute(query, task_ids)
        tags_map: defaultdict[str, list[str]] = defaultdict(list)
        for task_id, tag in cursor.fetchall():
            tags_map[task_id].append(tag)
        return dict(tags_map)

    if conn is not None:
        return _run(conn)
    with db.get_db() as c:
        return _run(c)


def load_tags_for_habits(
    habit_ids: list[str], conn: sqlite3.Connection | None = None
) -> dict[str, list[str]]:
    """Batch load all tags for multiple habits.

    Returns dict mapping habit_id -> list of tag strings.
    """
    if not habit_ids:
        return {}

    placeholders = ",".join("?" * len(habit_ids))
    query = f"SELECT habit_id, tag FROM tags WHERE habit_id IN ({placeholders}) ORDER BY tag"  # noqa: S608

    def _run(c: sqlite3.Connection) -> dict[str, list[str]]:
        cursor = c.execute(query, habit_ids)
        tags_map: defaultdict[str, list[str]] = defaultdict(list)
        for habit_id, tag in cursor.fetchall():
            tags_map[habit_id].append(tag)
        return dict(tags_map)

    if conn is not None:
        return _run(conn)
    with db.get_db() as c:
        return _run(c)


def hydrate_tags[T: (Task, Habit)](items: list[T], tag_map: dict[str, list[str]]) -> list[T]:
    """Apply tags to a list of items using a pre-loaded tag map.

    Args:
        items: List of Task or Habit objects
        tag_map: Dict mapping item.id -> list of tags

    Returns list of items with tags hydrated.
    """
    hydrated = []
    for item in items:
        direct_tags = tag_map.get(item.id, [])
        hydrated.append(hydrate_tags_onto(item, direct_tags))

    return hydrated
