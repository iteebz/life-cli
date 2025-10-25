import tempfile
from pathlib import Path

import pytest

from life.sqlite import (
    add_tag,
    add_task,
    check_reminder,
    complete_task,
    delete_task,
    get_context,
    get_pending_tasks,
    get_tags,
    get_tasks_by_tag,
    init_db,
    set_context,
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
        monkeypatch.setattr("life.sqlite.NEUROTYPE_PATH", tmp / "neurotype.txt")
        yield tmp


def test_init_creates_db(tmp_life_dir):
    init_db()
    assert (tmp_life_dir / "store.db").exists()


def test_add_task(tmp_life_dir):
    add_task("test task")
    tasks = get_pending_tasks()
    assert len(tasks) == 1
    assert tasks[0][1] == "test task"


def test_add_task_with_focus(tmp_life_dir):
    add_task("important", focus=True)
    tasks = get_pending_tasks()
    assert tasks[0][3] == 1


def test_add_task_with_due(tmp_life_dir):
    add_task("deadline", due="2025-12-31")
    tasks = get_pending_tasks()
    assert tasks[0][4] == "2025-12-31"


def test_complete_task(tmp_life_dir):
    add_task("task")
    tasks = get_pending_tasks()
    complete_task(tasks[0][0])
    assert len(get_pending_tasks()) == 0


def test_completed_task_excluded_from_pending(tmp_life_dir):
    add_task("a")
    add_task("b")
    tasks = get_pending_tasks()
    complete_task(tasks[0][0])
    remaining = get_pending_tasks()
    assert len(remaining) == 1
    assert remaining[0][1] == "b"


def test_toggle_focus(tmp_life_dir):
    add_task("task")
    tasks = get_pending_tasks()
    task_id, _, _, focus, *_ = tasks[0]
    assert focus == 0
    new_focus = toggle_focus(task_id, focus)
    assert new_focus == 1


def test_toggle_focus_twice(tmp_life_dir):
    add_task("task")
    tasks = get_pending_tasks()
    task_id = tasks[0][0]
    toggle_focus(task_id, 0)
    toggle_focus(task_id, 1)
    tasks = get_pending_tasks()
    assert tasks[0][3] == 0


def test_focus_noop_on_habits(tmp_life_dir):
    add_task("habit", category="habit")
    tasks = get_pending_tasks()
    task_id, _, cat, focus, *_ = tasks[0]
    new_focus = toggle_focus(task_id, focus, category=cat)
    assert new_focus == focus


def test_update_content(tmp_life_dir):
    add_task("old")
    tasks = get_pending_tasks()
    update_task(tasks[0][0], content="new")
    tasks = get_pending_tasks()
    assert tasks[0][1] == "new"


def test_update_due(tmp_life_dir):
    add_task("task")
    tasks = get_pending_tasks()
    update_task(tasks[0][0], due="2025-12-31")
    tasks = get_pending_tasks()
    assert tasks[0][4] == "2025-12-31"


def test_update_multiple_fields(tmp_life_dir):
    add_task("old")
    tasks = get_pending_tasks()
    task_id = tasks[0][0]
    update_task(task_id, content="new", due="2025-06-01", focus=True)
    tasks = get_pending_tasks()
    assert tasks[0][1] == "new"
    assert tasks[0][3] == 1
    assert tasks[0][4] == "2025-06-01"


def test_add_habit(tmp_life_dir):
    add_task("meditate", category="habit")
    tasks = get_pending_tasks()
    assert tasks[0][2] == "habit"


def test_add_chore(tmp_life_dir):
    add_task("dishes", category="chore")
    tasks = get_pending_tasks()
    assert tasks[0][2] == "chore"


def test_categories_mix(tmp_life_dir):
    add_task("task", category="task")
    add_task("habit", category="habit")
    add_task("chore", category="chore")
    tasks = get_pending_tasks()
    assert len(tasks) == 3
    assert {t[2] for t in tasks} == {"task", "habit", "chore"}


def test_check_habit(tmp_life_dir):
    add_task("hydrate", category="habit")
    tasks = get_pending_tasks()
    check_reminder(tasks[0][0])
    tasks = get_pending_tasks()
    assert tasks[0][2] == "habit"


def test_check_counts_to_completion(tmp_life_dir):
    from datetime import date, timedelta
    add_task("5x", category="habit", target_count=5)
    task_id = get_pending_tasks()[0][0]
    for i in range(5):
        check_date = (date.today() - timedelta(days=5-i)).isoformat()
        check_reminder(task_id, check_date)
    assert len(get_pending_tasks()) == 0


def test_check_duplicate_same_day_ignored(tmp_life_dir):
    add_task("check", category="habit")
    task_id = get_pending_tasks()[0][0]
    check_reminder(task_id)
    check_reminder(task_id)
    assert get_pending_tasks()[0][7] == 1


def test_add_tag(tmp_life_dir):
    add_task("task")
    task_id = get_pending_tasks()[0][0]
    add_tag(task_id, "urgent")
    tags = get_tags(task_id)
    assert "urgent" in tags


def test_duplicate_tag_ignored(tmp_life_dir):
    add_task("task")
    task_id = get_pending_tasks()[0][0]
    add_tag(task_id, "work")
    add_tag(task_id, "work")
    tags = get_tags(task_id)
    assert len(tags) == 1


def test_tag_case_normalized(tmp_life_dir):
    add_task("task")
    task_id = get_pending_tasks()[0][0]
    add_tag(task_id, "URGENT")
    tags = get_tags(task_id)
    assert "urgent" in tags


def test_get_tasks_by_tag(tmp_life_dir):
    add_task("a")
    add_task("b")
    add_tag(get_pending_tasks()[0][0], "focus")
    tagged = get_tasks_by_tag("focus")
    assert len(tagged) == 1
    assert tagged[0][1] == "a"


def test_context_lifecycle(tmp_life_dir):
    set_context("Wedding: 30 days")
    ctx = get_context()
    assert ctx == "Wedding: 30 days"
    assert (tmp_life_dir / "context.md").exists()


def test_delete_task(tmp_life_dir):
    add_task("a")
    add_task("b")
    task_id = get_pending_tasks()[0][0]
    delete_task(task_id)
    assert len(get_pending_tasks()) == 1


def test_delete_removes_tags(tmp_life_dir):
    add_task("a")
    task_id = get_pending_tasks()[0][0]
    add_tag(task_id, "focus")
    delete_task(task_id)
    assert len(get_tasks_by_tag("focus")) == 0


def test_pending_ordered_by_focus(tmp_life_dir):
    add_task("b")
    add_task("a", focus=True)
    tasks = get_pending_tasks()
    assert tasks[0][1] == "a"
    assert tasks[0][3] == 1


def test_pending_ordered_by_due(tmp_life_dir):
    add_task("later", due="2025-12-31")
    add_task("sooner", due="2025-01-01")
    tasks = get_pending_tasks()
    assert tasks[0][1] == "sooner"


def test_focus_trumps_due(tmp_life_dir):
    add_task("focus", focus=True, due="2025-12-31")
    add_task("due_soon", due="2025-01-01")
    tasks = get_pending_tasks()
    assert tasks[0][1] == "focus"
