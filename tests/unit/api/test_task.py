from life.api.tasks import (
    add_task,
    complete_task,
    delete_task,
    get_all_tasks,
    get_focus_tasks,
    get_pending_tasks,
    get_task,
    update_task,
)


def test_add_task_creates_task(tmp_life_dir):
    task_id = add_task("test task")
    assert task_id is not None
    task = get_task(task_id)
    assert task is not None
    assert task.content == "test task"


def test_add_task_with_focus(tmp_life_dir):
    task_id = add_task("focused task", focus=True)
    task = get_task(task_id)
    assert task.focus is True


def test_add_task_with_due(tmp_life_dir):
    task_id = add_task("due task", due="2025-12-31")
    task = get_task(task_id)
    assert str(task.due_date) == "2025-12-31"


def test_add_task_with_tags(tmp_life_dir):
    task_id = add_task("tagged task", tags=["urgent", "work"])
    task = get_task(task_id)
    assert "urgent" in task.tags
    assert "work" in task.tags


def test_get_pending_tasks(tmp_life_dir):
    add_task("task 1")
    add_task("task 2")
    tasks = get_pending_tasks()
    assert len(tasks) == 2


def test_get_all_tasks(tmp_life_dir):
    add_task("task 1")
    add_task("task 2")
    tasks = get_all_tasks()
    assert len(tasks) == 2


def test_complete_task(tmp_life_dir):
    task_id = add_task("task to complete")
    complete_task(task_id)
    pending = get_pending_tasks()
    assert not any(t.id == task_id for t in pending)


def test_get_focus_tasks(tmp_life_dir):
    task_id = add_task("focused", focus=True)
    add_task("unfocused", focus=False)
    focus_tasks = get_focus_tasks()
    assert len(focus_tasks) == 1
    assert focus_tasks[0].id == task_id


def test_update_task_content(tmp_life_dir):
    task_id = add_task("original")
    update_task(task_id, content="updated")
    task = get_task(task_id)
    assert task.content == "updated"


def test_update_task_focus(tmp_life_dir):
    task_id = add_task("task", focus=False)
    update_task(task_id, focus=True)
    task = get_task(task_id)
    assert task.focus is True


def test_update_task_due(tmp_life_dir):
    task_id = add_task("task", due="2025-12-31")
    update_task(task_id, due="2025-01-01")
    task = get_task(task_id)
    assert str(task.due_date) == "2025-01-01"


def test_delete_task(tmp_life_dir):
    task_id = add_task("task to delete")
    delete_task(task_id)
    task = get_task(task_id)
    assert task is None


def test_sort_pending_by_focus(tmp_life_dir):
    add_task("unfocused", focus=False)
    add_task("focused", focus=True)
    tasks = get_pending_tasks()
    assert tasks[0].focus is True


def test_sort_pending_by_due(tmp_life_dir):
    add_task("later", due="2025-12-31")
    add_task("sooner", due="2025-01-01")
    tasks = get_pending_tasks()
    assert str(tasks[0].due_date) == "2025-01-01"


def test_sort_focus_trumps_due(tmp_life_dir):
    add_task("unfocused soon", focus=False, due="2025-01-01")
    add_task("focused later", focus=True, due="2025-12-31")
    tasks = get_pending_tasks()
    assert tasks[0].focus is True
