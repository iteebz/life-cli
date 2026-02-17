import pytest
from click.exceptions import Exit

from life.lib.resolve import resolve_item, resolve_item_any, resolve_task
from life.tasks import add_task, toggle_completed


def test_resolve_task_finds_pending(tmp_life_dir):
    add_task("call the bank", tags=["finance"])
    task = resolve_task("call bank")
    assert task.content == "call the bank"


def test_resolve_task_does_not_find_completed(tmp_life_dir):
    task_id = add_task("completed thing", tags=["finance"])
    toggle_completed(task_id)
    with pytest.raises(Exit):
        resolve_task("completed thing")


def test_resolve_item_does_not_find_completed(tmp_life_dir):
    task_id = add_task("old task", tags=["finance"])
    toggle_completed(task_id)
    with pytest.raises(Exit):
        resolve_item("old task")


def test_resolve_item_any_finds_completed(tmp_life_dir):
    task_id = add_task("done task", tags=["finance"])
    toggle_completed(task_id)
    task, _ = resolve_item_any("done task")
    assert task is not None
    assert task.id == task_id


def test_resolve_item_any_prefers_pending(tmp_life_dir):
    pending_id = add_task("invoice jeff", tags=["finance"])
    completed_id = add_task("invoice jeff old", tags=["finance"])
    toggle_completed(completed_id)
    task, _ = resolve_item_any("invoice jeff")
    assert task.id == pending_id


def test_resolve_item_pending_only_not_history(tmp_life_dir):
    add_task("pending task", tags=["finance"])
    completed_id = add_task("completed task", tags=["finance"])
    toggle_completed(completed_id)
    task, _ = resolve_item("pending task")
    assert task is not None
    with pytest.raises(Exit):
        resolve_item("completed task")
