from life.api import add_item, complete_item, get_pending_items, get_today_completed


def test_store_add_item(tmp_life_dir):
    item_id = add_item("store item", item_type="habit", focus=False, due=None, tags=None)
    assert item_id is not None


def test_store_get_pending(tmp_life_dir):
    add_item("item 1", item_type="habit", focus=False, due=None, tags=None)
    add_item("item 2", item_type="habit", focus=False, due=None, tags=None)
    items = get_pending_items()
    item_id = add_item("task", item_type="task", focus=False, due=None, tags=None)
    complete_item(item_id)
    assert not any(item.id == item_id for item in items)


def test_store_get_completed_today(tmp_life_dir):
    item_id = add_item("task", item_type="task", focus=False, due=None, tags=None)
    complete_item(item_id)
    completed = get_today_completed()
    assert any(item.id == item_id for item in completed)
