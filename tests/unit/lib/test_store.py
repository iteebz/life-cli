from life.api import add_item, complete_item, get_pending_items, get_today_completed


def test_store_add_item(tmp_life_dir):
    item_id = add_item("store item", focus=False, due=None, is_repeat=True, tags=None)
    assert item_id is not None


def test_store_get_pending(tmp_life_dir):
    add_item("item 1", focus=False, due=None, is_repeat=True, tags=None)
    add_item("item 2", focus=False, due=None, is_repeat=True, tags=None)
    items = get_pending_items()
    assert len(items) >= 2

    item_id = add_item("task", focus=False, due=None, is_repeat=True, tags=None)
    complete_item(item_id)
    assert not any(item.id == item_id for item in items)


def test_store_get_completed_today(tmp_life_dir):
    item_id = add_item("task", focus=False, due=None, is_repeat=True, tags=None)
    complete_item(item_id)
    completed = get_today_completed()
    assert any(item.id == item_id for item in completed)
