from life.api import add_item, get_pending_items
from life.ops.toggle import toggle_done


def test_done_item_completes(tmp_life_dir):
    add_item("task to complete")
    items = get_pending_items()
    task = items[0] if items else None
    if task:
        result = toggle_done(task.content)
        assert result == ("task to complete", "done")


def test_done_item_undo(tmp_life_dir):
    add_item("task")
    items = get_pending_items()
    task = items[0] if items else None
    if task:
        toggle_done(task.content)
        result = toggle_done(task.content, undo=True)
        assert result == ("task", "undone")
