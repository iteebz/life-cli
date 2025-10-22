import tempfile
from pathlib import Path

import pytest

from life.sqlite import (
    add_task,
    check_reminder,
    complete_task,
    get_pending_tasks,
    init_db,
    toggle_focus,
    update_task,
)


@pytest.fixture
def tmp_life_dir(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        monkeypatch.setattr("life.sqlite.LIFE_DIR", tmp)
        monkeypatch.setattr("life.sqlite.DB_PATH", tmp / "store.db")
        monkeypatch.setattr("life.sqlite.CONTEXT_PATH", tmp / "context.md")
        yield tmp


def test_init_creates_db(tmp_life_dir):
    init_db()
    assert (tmp_life_dir / "store.db").exists()


def test_add_and_get_task(tmp_life_dir):
    add_task("test task")
    tasks = get_pending_tasks()
    assert len(tasks) == 1
    assert tasks[0][1] == "test task"


def test_complete_task(tmp_life_dir):
    add_task("task")
    tasks = get_pending_tasks()
    task_id = tasks[0][0]
    complete_task(task_id)
    assert len(get_pending_tasks()) == 0


def test_toggle_focus(tmp_life_dir):
    add_task("task")
    tasks = get_pending_tasks()
    task_id, _content, _cat, focus, _due, _created = tasks[0]
    assert focus == 0
    new_focus = toggle_focus(task_id, focus)
    assert new_focus == 1


def test_update_task(tmp_life_dir):
    add_task("old")
    tasks = get_pending_tasks()
    task_id = tasks[0][0]
    update_task(task_id, content="new", due="2025-12-31")
    tasks = get_pending_tasks()
    assert tasks[0][1] == "new"
    assert tasks[0][4] == "2025-12-31"


def test_add_habit(tmp_life_dir):
    add_task("meditate", category="habit")
    tasks = get_pending_tasks()
    assert len(tasks) == 1
    assert tasks[0][2] == "habit"


def test_add_chore(tmp_life_dir):
    add_task("dishes", category="chore")
    tasks = get_pending_tasks()
    assert len(tasks) == 1
    assert tasks[0][2] == "chore"


def test_check_habit(tmp_life_dir):
    add_task("hydrate", category="habit")
    tasks = get_pending_tasks()
    habit_id = tasks[0][0]
    check_reminder(habit_id)
    tasks = get_pending_tasks()
    assert len(tasks) == 1
    assert tasks[0][2] == "habit"
