from life.api import (
    add_item,
    delete_item,
    get_pending_items,
    get_today_completed,
    update_item,
)
from life.ops.items import remove, update
from life.ops.toggle import toggle_done
from life.ops.toggle import toggle_focus as toggle_item_focus


def test_add_item_creates_item(tmp_life_dir):
    item_id = add_item("test item")
    assert item_id is not None
    items = get_pending_items()
    assert any(item.content == "test item" for item in items)


def test_add_item_with_focus(tmp_life_dir):
    item_id = add_item("focused task", focus=True)
    items = get_pending_items()
    item = next((i for i in items if i.id == item_id), None)
    assert item is not None
    assert item.focus is True


def test_add_item_with_due(tmp_life_dir):
    item_id = add_item("due task", due="2025-12-31")
    items = get_pending_items()
    item = next((i for i in items if i.id == item_id), None)
    assert item is not None
    assert str(item.due) == "2025-12-31"


def test_add_item_with_tags(tmp_life_dir):
    item_id = add_item("tagged item", tags=["urgent", "work"])
    items = get_pending_items()
    item = next((i for i in items if i.id == item_id), None)
    assert item is not None


def test_get_pending_items(tmp_life_dir):
    add_item("item 1")
    add_item("item 2")
    items = get_pending_items()
    assert len(items) >= 2


def test_complete_item(tmp_life_dir):
    item_id = add_item("task to complete")
    toggle_done(str(item_id))
    pending = get_pending_items()
    assert not any(item.id == item_id for item in pending)


def test_uncomplete_item(tmp_life_dir):
    item_id = add_item("task to complete")
    toggle_done(str(item_id))
    toggle_done(str(item_id), undo=True)
    pending = get_pending_items()
    assert any(item.id == item_id for item in pending)


def test_toggle_focus(tmp_life_dir):
    item_id = add_item("task", focus=False)
    new_focus = toggle_item_focus(item_id, False)
    assert new_focus
    new_focus = toggle_item_focus(item_id, True)
    assert not new_focus


def test_update_item_content(tmp_life_dir):
    item_id = add_item("original content")
    update_item(item_id, content="updated content")
    items = get_pending_items()
    item = next((i for i in items if i.id == item_id), None)
    assert item.content == "updated content"


def test_update_item_due(tmp_life_dir):
    item_id = add_item("task", due="2025-12-31")
    update_item(item_id, due="2025-12-25")
    items = get_pending_items()
    item = next((i for i in items if i.id == item_id), None)
    assert str(item.due) == "2025-12-25"


def test_delete_item(tmp_life_dir):
    item_id = add_item("task to delete")
    delete_item(item_id)
    items = get_pending_items()
    assert not any(item.id == item_id for item in items)


def test_get_today_completed(tmp_life_dir):
    item_id = add_item("task")
    toggle_done(str(item_id))
    completed = get_today_completed()
    assert any(item.id == item_id for item in completed)


def test_complete_command(tmp_life_dir):
    item_id = add_item("task to complete")
    status, content = toggle_done(str(item_id))
    assert status == "Done"
    assert content == "task to complete"


def test_uncomplete_command(tmp_life_dir):
    item_id = add_item("task")
    toggle_done(str(item_id))
    status, content = toggle_done(str(item_id), undo=True)
    assert status == "Pending"
    assert content == "task"


def test_toggle_focus_partial(tmp_life_dir):
    item_id = add_item("task", focus=False)
    status_text, content = toggle_item_focus(item_id, False)
    assert status_text is not None
    assert status_text in ("Focused", "Unfocused")


def test_toggle_focus_fails_on_habit(tmp_life_dir):
    habit_id = add_item("habit", is_habit=True, tags=["habit"])
    # toggle_item_focus expects item_id and current_focus, not partial string
    # This test case needs to be re-evaluated based on how habits handle focus
    # For now, we'll assert that directly calling toggle_item_focus on a habit doesn't change its focus status
    item = next((i for i in get_pending_items() if i.id == habit_id), None)
    assert item is not None
    original_focus = item.focus
    toggle_item_focus(habit_id, original_focus)
    item_after_toggle = next((i for i in get_pending_items() if i.id == habit_id), None)
    assert item_after_toggle.focus == original_focus


def test_update_command(tmp_life_dir):
    item_id = add_item("original")
    result = update(str(item_id), content="updated")
    assert result == "updated"


def test_delete_command(tmp_life_dir):
    item_id = add_item("task to remove")
    result = remove(str(item_id))
    assert result is not None
    pending = get_pending_items()
    assert not any(item.id == item_id for item in pending)


def test_add(tmp_life_dir):
    add_item("task")
    items = get_pending_items()
    assert len(items) == 1
    assert items[0].content == "task"


def test_focus_on_add(tmp_life_dir):
    add_item("urgent", focus=True)
    items = get_pending_items()
    assert items[0].focus is True


def test_due_on_add(tmp_life_dir):
    add_item("deadline", due="2025-12-31")
    items = get_pending_items()
    assert str(items[0].due) == "2025-12-31"


def test_complete(tmp_life_dir):
    item_id = add_item("task")
    toggle_done(str(item_id))
    assert len(get_pending_items()) == 0


def test_focus_toggle(tmp_life_dir):
    iid = add_item("task")
    new_state = toggle_item_focus(iid, False)
    assert new_state
    items = get_pending_items()
    assert items[0].focus is True


def test_update_content(tmp_life_dir):
    iid = add_item("old")
    update_item(iid, content="new")
    items = get_pending_items()
    assert items[0].content == "new"


def test_update_due(tmp_life_dir):
    iid = add_item("task")
    update_item(iid, due="2025-06-01")
    items = get_pending_items()
    assert str(items[0].due) == "2025-06-01"


def test_delete(tmp_life_dir):
    iid_a = add_item("a")
    iid_b = add_item("b")
    delete_item(iid_a)
    remaining_items = get_pending_items()
    assert len(remaining_items) == 1
    assert remaining_items[0].id == iid_b
    assert remaining_items[0].content == "b"


def test_sort_by_focus(tmp_life_dir):
    add_item("low")
    add_item("high", focus=True)
    items = get_pending_items()
    assert items[0].focus == 1


def test_sort_by_due(tmp_life_dir):
    add_item("later", due="2025-12-31")
    add_item("sooner", due="2025-01-01")
    items = get_pending_items()
    assert items[0].content == "sooner"


def test_focus_trumps_due(tmp_life_dir):
    add_item("low", due="2025-01-01")
    add_item("high", focus=True, due="2025-12-31")
    items = get_pending_items()
    assert items[0].focus == 1
