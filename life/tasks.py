import contextlib
import re
import sqlite3
import sys
import uuid
from datetime import date as _date
from datetime import datetime, timedelta

from . import db
from .lib import clock
from .lib.ansi import ANSI
from .lib.converters import row_to_task
from .lib.errors import echo, exit_error
from .lib.format import format_status
from .lib.fuzzy import find_in_pool, find_in_pool_exact
from .lib.parsing import parse_due_and_item, validate_content
from .models import Task, TaskMutation
from .tags import add_tag, hydrate_tags, load_tags_for_tasks

__all__ = [
    "add_link",
    "add_task",
    "cancel_task",
    "check_task",
    "cmd_block",
    "cmd_cancel",
    "cmd_defer",
    "cmd_due",
    "cmd_focus",
    "cmd_link",
    "cmd_now",
    "cmd_rename_task",
    "cmd_schedule",
    "cmd_set",
    "cmd_show",
    "cmd_task",
    "cmd_today",
    "cmd_tomorrow",
    "cmd_unblock",
    "cmd_unfocus",
    "cmd_unlink",
    "count_overdue_resets",
    "defer_task",
    "delete_task",
    "find_task",
    "find_task_any",
    "find_task_exact",
    "get_all_links",
    "get_all_tasks",
    "get_focus",
    "get_links",
    "get_mutations",
    "get_subtasks",
    "get_task",
    "get_tasks",
    "last_completion",
    "remove_link",
    "set_blocked_by",
    "toggle_completed",
    "toggle_focus",
    "uncheck_task",
    "update_task",
]


def _task_sort_key(task: Task) -> tuple[bool, bool, object, object]:
    """Canonical sort order: focus first, then by scheduled date, then by creation."""
    return (
        not task.focus,
        task.scheduled_date is None,
        task.scheduled_date,
        task.created,
    )


_AUTOTAG_PATTERNS = {
    "comms": re.compile(
        r"\b(call|message|whatsapp|email|voicemail|reply|text|telegram|signal)\b", re.IGNORECASE
    ),
    "finance": re.compile(
        r"\b(invoice|pay|transfer|liquidate|buy|order|purchase|refund|deposit)\b", re.IGNORECASE
    ),
    "health": re.compile(
        r"\b(dentist|doctor|physio|health|medical|pharmacy|chemist)\b", re.IGNORECASE
    ),
}


def _autotag(content: str, existing_tags: list[str] | None) -> list[str]:
    """Auto-add tags based on content patterns. Returns new tags to add."""
    if existing_tags is None:
        existing_tags = []
    existing_normalized = [t.lstrip("#") for t in existing_tags]
    content_lower = content.lower()
    new_tags = []
    for tag, pattern in _AUTOTAG_PATTERNS.items():
        if tag not in existing_normalized and pattern.search(content_lower):
            new_tags.append(tag)
    return new_tags


def add_task(
    content: str,
    focus: bool = False,
    scheduled_date: str | None = None,
    tags: list[str] | None = None,
    parent_id: str | None = None,
    description: str | None = None,
    steward: bool = False,
    source: str | None = None,
) -> str:
    """Adds a new task. Returns task_id."""
    task_id = str(uuid.uuid4())
    with db.get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO tasks (id, content, focus, scheduled_date, created, parent_id, description, steward, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    task_id,
                    content,
                    focus,
                    scheduled_date,
                    clock.today().isoformat(),
                    parent_id,
                    description,
                    steward,
                    source,
                ),
            )
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to add task: {e}") from e

        all_tags = list(tags or [])
        all_tags.extend(_autotag(content, all_tags))

        for tag in all_tags:
            add_tag(task_id, None, tag, conn=conn)
    return task_id


def get_task(task_id: str) -> Task | None:
    """SELECT from tasks + LEFT JOIN tags, return Task or None."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, scheduled_date, created, completed_at, parent_id, scheduled_time, blocked_by, description, steward, source, deadline_date, deadline_time FROM tasks WHERE id = ?",
            (task_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        task = row_to_task(row)
        tags_map = load_tags_for_tasks([task_id], conn=conn)
        return hydrate_tags([task], tags_map)[0]


def get_tasks(include_steward: bool = False) -> list[Task]:
    """SELECT pending (incomplete) tasks, sorted by (focus DESC, due_date ASC, created ASC)."""
    with db.get_db() as conn:
        if include_steward:
            cursor = conn.execute(
                "SELECT id, content, focus, scheduled_date, created, completed_at, parent_id, scheduled_time, blocked_by, description, steward, source, deadline_date, deadline_time FROM tasks WHERE completed_at IS NULL"
            )
        else:
            cursor = conn.execute(
                "SELECT id, content, focus, scheduled_date, created, completed_at, parent_id, scheduled_time, blocked_by, description, steward, source, deadline_date, deadline_time FROM tasks WHERE completed_at IS NULL AND steward = 0"
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
            "SELECT id, content, focus, scheduled_date, created, completed_at, parent_id, scheduled_time, blocked_by, description, steward, source, deadline_date, deadline_time FROM tasks WHERE steward = 0"
        )
        tasks = [row_to_task(row) for row in cursor.fetchall()]
        task_ids = [t.id for t in tasks]
        tags_map = load_tags_for_tasks(task_ids, conn=conn)
        result = hydrate_tags(tasks, tags_map)

    return sorted(result, key=_task_sort_key)


def get_subtasks(parent_id: str) -> list[Task]:
    """Return all tasks with the given parent_id."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, scheduled_date, created, completed_at, parent_id, scheduled_time, blocked_by, description, steward, source, deadline_date, deadline_time FROM tasks WHERE parent_id = ?",
            (parent_id,),
        )
        tasks = [row_to_task(row) for row in cursor.fetchall()]
        task_ids = [t.id for t in tasks]
        tags_map = load_tags_for_tasks(task_ids, conn=conn)
        return hydrate_tags(tasks, tags_map)


def get_focus() -> list[Task]:
    """SELECT focus = 1 AND completed_at IS NULL."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, scheduled_date, created, completed_at, parent_id, scheduled_time, blocked_by, description, steward, source, deadline_date, deadline_time FROM tasks WHERE focus = 1 AND completed_at IS NULL AND steward = 0"
        )
        tasks = [row_to_task(row) for row in cursor.fetchall()]
        task_ids = [t.id for t in tasks]
        tags_map = load_tags_for_tasks(task_ids, conn=conn)
        return hydrate_tags(tasks, tags_map)


_TRACKED_FIELDS = {"content", "scheduled_date", "scheduled_time", "deadline_date", "deadline_time", "focus", "completed_at"}


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


_UNSET: object = object()
UNSET = _UNSET


def update_task(
    task_id: str,
    content: str | None = None,
    focus: bool | None = None,
    scheduled_date: str | object = _UNSET,
    scheduled_time: str | object = _UNSET,
    deadline_date: str | object = _UNSET,
    deadline_time: str | object = _UNSET,
    parent_id: str | object = _UNSET,
    description: str | object = _UNSET,
) -> Task | None:
    """Partial update, return updated Task. Pass None to clear a nullable field."""
    updates = {}
    if content is not None:
        updates["content"] = content
    if focus is not None:
        updates["focus"] = focus
    if scheduled_date is not _UNSET:
        updates["scheduled_date"] = scheduled_date
    if scheduled_time is not _UNSET:
        updates["scheduled_time"] = scheduled_time
    if deadline_date is not _UNSET:
        updates["deadline_date"] = deadline_date
    if deadline_time is not _UNSET:
        updates["deadline_time"] = deadline_time
    if parent_id is not _UNSET:
        updates["parent_id"] = parent_id
    if description is not _UNSET:
        updates["description"] = description

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


def count_overdue_resets(window_start: str, window_end: str) -> int:
    """Count overdue_reset deferrals within a date window (ISO strings)."""
    with db.get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM task_mutations WHERE reason = 'overdue_reset' AND date(mutated_at) >= ? AND date(mutated_at) <= ?",
            (window_start, window_end),
        ).fetchone()
    return row[0] if row else 0


def cancel_task(task_id: str, reason: str) -> None:
    """Cancel a task: preserved in deleted_tasks with cancel_reason for analytics."""
    with db.get_db() as conn:
        row = conn.execute("SELECT id, content FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row:
            tag_rows = conn.execute("SELECT tag FROM tags WHERE task_id = ?", (task_id,)).fetchall()
            tags_str = ",".join(r[0] for r in tag_rows) if tag_rows else None
            conn.execute(
                "INSERT INTO deleted_tasks (task_id, content, tags, cancel_reason, cancelled) VALUES (?, ?, ?, ?, 1)",
                (row[0], row[1], tags_str, reason),
            )
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def delete_task(task_id: str) -> None:
    """DELETE from tasks. Writes audit record to deleted_tasks first."""
    with db.get_db() as conn:
        row = conn.execute("SELECT id, content FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row:
            tag_rows = conn.execute("SELECT tag FROM tags WHERE task_id = ?", (task_id,)).fetchall()
            tags_str = ",".join(r[0] for r in tag_rows) if tag_rows else None
            conn.execute(
                "INSERT INTO deleted_tasks (task_id, content, tags) VALUES (?, ?, ?)",
                (row[0], row[1], tags_str),
            )
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def check_task(task_id: str) -> tuple[Task | None, Task | None]:
    """Mark task as complete. Returns (task, parent_if_set_completed)."""
    task = get_task(task_id)
    if not task or task.completed_at:
        return task, None
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
    completed_task = get_task(task_id)
    parent_completed = None
    if task.parent_id:
        siblings = get_subtasks(task.parent_id)
        if all(s.completed_at for s in siblings):
            parent = get_task(task.parent_id)
            if parent and not parent.completed_at:
                with db.get_db() as conn:
                    conn.execute(
                        "UPDATE tasks SET completed_at = ? WHERE id = ?",
                        (completed, task.parent_id),
                    )
                    _record_mutation(conn, task.parent_id, "completed_at", None, completed)
                parent_completed = get_task(task.parent_id)
    return completed_task, parent_completed


def uncheck_task(task_id: str) -> Task | None:
    """Mark task as pending. Reopens parent if set was complete."""
    task = get_task(task_id)
    if not task or not task.completed_at:
        return task
    with db.get_db() as conn:
        conn.execute("UPDATE tasks SET completed_at = NULL WHERE id = ?", (task_id,))
        _record_mutation(conn, task_id, "completed_at", task.completed_at, None)
    if task.parent_id:
        parent = get_task(task.parent_id)
        if parent and parent.completed_at:
            with db.get_db() as conn:
                conn.execute("UPDATE tasks SET completed_at = NULL WHERE id = ?", (task.parent_id,))
                _record_mutation(conn, task.parent_id, "completed_at", parent.completed_at, None)
    return get_task(task_id)


def toggle_completed(task_id: str) -> Task | None:
    """Toggle task completion."""
    task = get_task(task_id)
    if not task:
        return None
    if task.completed_at:
        return uncheck_task(task_id)
    task, _ = check_task(task_id)
    return task


def toggle_focus(task_id: str) -> Task | None:
    """Toggle task focus status."""
    task = get_task(task_id)
    if not task:
        return None

    new_focus = not task.focus
    return update_task(task_id, focus=new_focus)


def find_task(ref: str) -> Task | None:
    from .dashboard import _get_completed_today

    pending = get_tasks(include_steward=True)
    completed_today = _get_completed_today()
    return find_in_pool(ref, pending + completed_today)


def find_task_any(ref: str) -> Task | None:
    return find_in_pool(ref, get_all_tasks())


def find_task_exact(ref: str) -> Task | None:
    from .dashboard import _get_completed_today

    pending = get_tasks(include_steward=True)
    completed_today = _get_completed_today()
    return find_in_pool_exact(ref, pending + completed_today)


def get_all_links() -> list[tuple[str, str]]:
    """Return all (from_id, to_id) pairs from task_links."""
    with db.get_db() as conn:
        rows = conn.execute("SELECT from_id, to_id FROM task_links").fetchall()
    return [(r[0], r[1]) for r in rows]


def add_link(from_id: str, to_id: str) -> None:
    with db.get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO task_links (from_id, to_id) VALUES (?, ?)",
            (from_id, to_id),
        )


def remove_link(from_id: str, to_id: str) -> None:
    with db.get_db() as conn:
        conn.execute(
            "DELETE FROM task_links WHERE (from_id = ? AND to_id = ?) OR (from_id = ? AND to_id = ?)",
            (from_id, to_id, to_id, from_id),
        )


def get_links(task_id: str) -> list[Task]:
    """Return all tasks linked to/from task_id."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, scheduled_date, created, completed_at, parent_id, scheduled_time, blocked_by, description, steward, source, deadline_date, deadline_time FROM tasks WHERE id IN (SELECT to_id FROM task_links WHERE from_id = ? UNION SELECT from_id FROM task_links WHERE to_id = ?)",
            (task_id, task_id),
        )
        tasks = [row_to_task(row) for row in cursor.fetchall()]
        task_ids = [t.id for t in tasks]
        tags_map = load_tags_for_tasks(task_ids, conn=conn)
        return hydrate_tags(tasks, tags_map)


def set_blocked_by(task_id: str, blocker_id: str | None) -> Task | None:
    """Set or clear the blocked_by pointer on a task."""
    with db.get_db() as conn:
        conn.execute(
            "UPDATE tasks SET blocked_by = ? WHERE id = ?",
            (blocker_id, task_id),
        )
    return get_task(task_id)


def last_completion() -> datetime | None:
    """Return the most recent completion timestamp across tasks and habit checks."""
    with db.get_db() as conn:
        task_row = conn.execute(
            "SELECT completed_at FROM tasks WHERE completed_at IS NOT NULL ORDER BY completed_at DESC LIMIT 1"
        ).fetchone()
        check_row = conn.execute(
            "SELECT completed_at FROM checks ORDER BY completed_at DESC LIMIT 1"
        ).fetchone()
    candidates: list[datetime] = []
    for row in (task_row, check_row):
        if row and row[0]:
            with contextlib.suppress(ValueError):
                candidates.append(datetime.fromisoformat(row[0]))
    return max(candidates) if candidates else None


def _animate_check(label: str) -> None:
    sys.stdout.write(f"  {ANSI.GREEN}\u2713{ANSI.RESET} {ANSI.GREY}{label}{ANSI.RESET}\n")
    sys.stdout.flush()


def cmd_task(
    content_args: list[str],
    focus: bool = False,
    due: str | None = None,
    tags: list[str] | None = None,
    under: str | None = None,
    description: str | None = None,
    done: bool = False,
    steward: bool = False,
    source: str | None = None,
) -> None:
    from .lib.resolve import resolve_task
    content = " ".join(content_args) if content_args else ""
    try:
        validate_content(content)
    except ValueError as e:
        exit_error(f"Error: {e}")
    resolved_due = None
    resolved_time = None
    if due:
        from .lib.parsing import parse_due_datetime
        resolved_due, resolved_time = parse_due_datetime(due)
    parent_id = None
    if under:
        parent_task = resolve_task(under)
        if parent_task.parent_id:
            exit_error("Error: subtasks cannot have subtasks")
        parent_id = parent_task.id
    if focus and parent_id:
        exit_error("Error: cannot focus a subtask — set focus on the parent")
    task_id = add_task(
        content,
        focus=focus,
        scheduled_date=resolved_due,
        tags=tags,
        parent_id=parent_id,
        description=description,
        steward=steward,
        source=source,
    )
    if resolved_due or resolved_time:
        updates: dict = {}
        if resolved_due:
            updates["deadline_date"] = resolved_due
        if resolved_time:
            updates["deadline_time"] = resolved_time
        update_task(task_id, **updates)
    if done:
        check_task(task_id)
        echo(format_status("\u2713", content, task_id))
        return
    symbol = f"{ANSI.BOLD}\u29bf{ANSI.RESET}" if focus else "\u25a1"
    prefix = "  \u2514 " if parent_id else ""
    echo(f"{prefix}{format_status(symbol, content, task_id)}")


def cmd_check_task(task: Task) -> None:
    if task.completed_at:
        exit_error(f"'{task.content}' is already done")
    _, parent_completed = check_task(task.id)
    _animate_check(task.content.lower())
    if parent_completed:
        _animate_check(parent_completed.content.lower())


def cmd_focus(args: list[str]) -> None:
    from .lib.resolve import resolve_task
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life focus <item>")
    task = resolve_task(ref)
    toggle_focus(task.id)
    symbol = f"{ANSI.BOLD}\u29bf{ANSI.RESET}" if not task.focus else "\u25a1"
    echo(format_status(symbol, task.content, task.id))


def cmd_unfocus(args: list[str]) -> None:
    from .lib.resolve import resolve_task
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life unfocus <item>")
    task = resolve_task(ref)
    if not task.focus:
        exit_error(f"'{task.content}' is not focused")
    toggle_focus(task.id)
    echo(format_status("\u25a1", task.content, task.id))


def cmd_due(args: list[str], remove: bool = False) -> None:
    from .lib.resolve import resolve_task
    try:
        date_str, time_str, item_name = parse_due_and_item(args, remove=remove)
    except ValueError as e:
        exit_error(str(e))
    task = resolve_task(item_name)
    if remove:
        update_task(task.id, deadline_date=None, deadline_time=None)
        echo(format_status("\u25a1", task.content, task.id))
        return
    if not date_str and not time_str:
        exit_error(
            "Due spec required: today, tomorrow, day name, YYYY-MM-DD, HH:MM, 'now', or -r to clear"
        )
    updates: dict = {}
    if date_str:
        updates["deadline_date"] = date_str
    if time_str:
        updates["deadline_time"] = time_str
    update_task(task.id, **updates)
    if time_str:
        label = f"{ANSI.GREY}{time_str}{ANSI.RESET}"
    else:
        due = _date.fromisoformat(date_str)
        delta = (due - clock.today()).days
        label = f"{ANSI.GREY}+{delta}d{ANSI.RESET}"
    echo(format_status(label, task.content, task.id))


def cmd_set(
    args: list[str],
    parent: str | None = None,
    content: str | None = None,
    description: str | None = None,
) -> None:
    from .lib.resolve import resolve_task
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life set <task> [-p parent] [-c content]")
    task = resolve_task(ref)
    parent_id: str | None = None
    has_update = False
    if parent is not None:
        parent_task = resolve_task(parent)
        if parent_task.parent_id:
            exit_error("Error: subtasks cannot have subtasks")
        if parent_task.id == task.id:
            exit_error("Error: a task cannot be its own parent")
        if task.focus:
            exit_error("Error: cannot parent a focused task — unfocus first")
        parent_id = parent_task.id
        has_update = True
    if content is not None:
        if not content.strip():
            exit_error("Error: content cannot be empty")
        has_update = True
    desc: str | None = None
    if description is not None:
        desc = description if description != "" else None
        has_update = True
    if not has_update:
        exit_error("Nothing to set. Use -p for parent, -c for content, or -d for description.")
    update_task(
        task.id,
        content=content,
        parent_id=parent_id if parent is not None else UNSET,
        description=desc if description is not None else UNSET,
    )
    updated = resolve_task(content or ref)
    prefix = "  \u2514 " if updated.parent_id else ""
    from .lib.format import format_status as _fs
    echo(f"{prefix}{_fs('\u25a1', updated.content, updated.id)}")


def cmd_show(args: list[str]) -> None:
    from .lib.render import render_task_detail
    from .lib.resolve import resolve_task
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life show <task>")
    task = resolve_task(ref)
    subtasks = get_subtasks(task.id)
    linked = get_links(task.id)
    mutations = get_mutations(task.id)
    echo(render_task_detail(task, subtasks, linked, mutations))


def cmd_link(a_args: list[str], b_args: list[str]) -> None:
    from .lib.resolve import resolve_task
    a = resolve_task(" ".join(a_args))
    b = resolve_task(" ".join(b_args))
    if a.id == b.id:
        exit_error("Cannot link a task to itself")
    add_link(a.id, b.id)
    echo(f"{a.content.lower()} {ANSI.GREY}~ {b.content.lower()}{ANSI.RESET}")


def cmd_unlink(a_args: list[str], b_args: list[str]) -> None:
    from .lib.resolve import resolve_task
    a = resolve_task(" ".join(a_args))
    b = resolve_task(" ".join(b_args))
    remove_link(a.id, b.id)
    echo(f"{a.content.lower()} {ANSI.GREY}\u2717 {b.content.lower()}{ANSI.RESET}")


def cmd_block(blocked_args: list[str], blocker_args: list[str]) -> None:
    from .lib.resolve import resolve_task
    blocked = resolve_task(" ".join(blocked_args))
    blocker = resolve_task(" ".join(blocker_args))
    if blocker.id == blocked.id:
        exit_error("A task cannot block itself")
    set_blocked_by(blocked.id, blocker.id)
    echo(f"\u2298 {blocked.content.lower()}  \u2190  {blocker.content.lower()}")


def cmd_unblock(args: list[str]) -> None:
    from .lib.resolve import resolve_task
    task = resolve_task(" ".join(args))
    if not task.blocked_by:
        exit_error(f"'{task.content}' is not blocked")
    set_blocked_by(task.id, None)
    echo(f"\u25a1 {task.content.lower()}  unblocked")


def cmd_cancel(args: list[str], reason: str | None) -> None:
    from .lib.resolve import resolve_task
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life cancel <task> --reason <why>")
    if not reason:
        exit_error("--reason required. Why are you cancelling this?")
    task = resolve_task(ref)
    cancel_task(task.id, reason)
    echo(f"\u2717 {task.content.lower()} \u2014 {reason}")


def cmd_defer(args: list[str], reason: str | None) -> None:
    from .lib.resolve import resolve_task
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life defer <task> --reason <why>")
    if not reason:
        exit_error("--reason required. Why are you deferring this?")
    task = resolve_task(ref)
    defer_task(task.id, reason)
    echo(f"\u2192 {task.content.lower()} deferred: {reason}")


def cmd_rename_task(task: Task, to_content: str) -> None:
    if task.content == to_content:
        exit_error(f"Error: Cannot rename '{task.content}' to itself.")
    update_task(task.id, content=to_content)
    echo(f"\u2192 {to_content}")


def cmd_now(args: list[str]) -> None:
    cmd_schedule(["now"] + list(args))


def cmd_today(args: list[str]) -> None:
    cmd_schedule(["today"] + list(args))


def cmd_tomorrow(args: list[str]) -> None:
    cmd_schedule(["tomorrow"] + list(args))


def cmd_schedule(args: list[str], remove: bool = False) -> None:
    from .lib.resolve import resolve_task
    if remove:
        if not args:
            exit_error("Usage: life schedule -r <task>")
        try:
            _, _, item_name = parse_due_and_item(list(args), remove=True)
        except ValueError as e:
            exit_error(str(e))
        task = resolve_task(item_name)
        update_task(task.id, scheduled_date=None, scheduled_time=None)
        echo(format_status("\u25a1", task.content, task.id))
        return
    try:
        date_str, time_str, item_name = parse_due_and_item(list(args))
    except ValueError as e:
        exit_error(str(e))
    if not date_str and not time_str:
        exit_error(
            "Schedule spec required: today, tomorrow, day name, YYYY-MM-DD, HH:MM, or 'now'"
        )
    task = resolve_task(item_name)
    updates: dict = {}
    if date_str:
        updates["scheduled_date"] = date_str
    if time_str:
        updates["scheduled_time"] = time_str
    update_task(task.id, **updates)
    if time_str:
        label = f"{ANSI.GREY}{time_str}{ANSI.RESET}"
    else:
        d = _date.fromisoformat(date_str)
        delta = (d - clock.today()).days
        label = f"{ANSI.GREY}+{delta}d{ANSI.RESET}"
    echo(format_status(label, task.content, task.id))
