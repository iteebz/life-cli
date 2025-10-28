from life.api import add_item, get_pending_items
from life.ops import done_item


def test_done_item_completes(tmp_life_dir):
    add_item("task to complete")
    items = get_pending_items()
    task = items[0] if items else None
    if task:
        result = done_item(task.content)
        assert "✓" in result


def test_done_item_undo(tmp_life_dir):
    add_item("task")
    items = get_pending_items()
    task = items[0] if items else None
    if task:
        done_item(task.content)
        result = done_item(task.content, undo=True)
        assert "✓" in result
