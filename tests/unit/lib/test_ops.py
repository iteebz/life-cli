import pytest

from life.lib.ops import complete, remove, set_due, toggle, uncomplete, update


def test_complete_task(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("complete me")
    result = complete("complete")
    assert result == "complete me"
    assert len(get_pending_items()) == 0


def test_complete_habit_increments_count(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("meditate", tags=["habit"])
    result = complete("meditate")
    assert result == "meditate"
    items = get_pending_items()
    assert len(items) == 1
    assert items[0][6] == 1


def test_complete_nonexistent():
    assert complete("nonexistent") is None


def test_uncomplete_from_today(tmp_life_dir):
    from life.core.item import add_item, complete_item

    iid = add_item("undo me")
    complete_item(iid)
    result = uncomplete("undo")
    assert result == "undo me"


def test_uncomplete_not_today(tmp_life_dir):
    import sqlite3
    from datetime import date, timedelta

    from life.core.item import add_item
    from life.lib.sqlite import DB_PATH

    iid = add_item("old")
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE items SET completed = ? WHERE id = ?", (yesterday, iid))
    conn.commit()
    conn.close()
    assert uncomplete("old") is None


@pytest.mark.parametrize("tag", ["habit", "chore"])
def test_toggle_fails_on_non_task(tmp_life_dir, tag):
    from life.core.item import add_item

    add_item("item", tags=[tag])
    assert toggle("item") is None


def test_toggle_on(tmp_life_dir):
    from life.core.item import add_item

    add_item("unfocused")
    result = toggle("unfocused")
    assert result and result[0] == "Focused"


def test_toggle_off(tmp_life_dir):
    from life.core.item import add_item

    add_item("focused", focus=True)
    result = toggle("focused")
    assert result and result[0] == "Unfocused"


def test_update_content(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("old content")
    result = update("old", content="new content")
    assert result == "new content"
    assert get_pending_items()[0][1] == "new content"


def test_update_due(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("task")
    result = update("task", due="2025-12-31")
    assert result == "task"
    assert get_pending_items()[0][3] == "2025-12-31"


@pytest.mark.parametrize("tag", ["habit", "chore"])
def test_update_focus_fails_on_non_task(tmp_life_dir, tag):
    from life.core.item import add_item

    add_item("item", tags=[tag])
    assert update("item", focus=True) is None


def test_remove_item(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("delete me")
    result = remove("delete")
    assert result == "delete me"
    assert len(get_pending_items()) == 0


def test_remove_completed_today(tmp_life_dir):
    from life.core.item import add_item, complete_item, get_today_completed

    iid = add_item("completed task")
    complete_item(iid)
    result = remove("completed")
    assert result == "completed task"
    assert len(get_today_completed()) == 0


def test_remove_prefers_pending(tmp_life_dir):
    from life.core.item import add_item, complete_item, get_pending_items, get_today_completed

    iid_completed = add_item("match")
    complete_item(iid_completed)
    add_item("match")
    result = remove("match")
    assert result == "match"
    assert len(get_pending_items()) == 0
    assert len(get_today_completed()) == 1


def test_remove_lifo(tmp_life_dir):
    import time

    from life.core.item import add_item, get_pending_items

    for _ in range(3):
        add_item("remove me")
        time.sleep(0.01)

    initial = len(get_pending_items())
    for i in range(3):
        result = remove("remove me")
        assert result == "remove me"
        assert len(get_pending_items()) == initial - (i + 1)


def test_remove_nonexistent():
    assert remove("nonexistent") is None


def test_set_due_with_date(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("deadline task")
    result = set_due(["2025-12-31", "deadline"])
    assert "2025-12-31" in result
    assert get_pending_items()[0][3] == "2025-12-31"


def test_set_due_remove(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("task", due="2025-12-31")
    result = set_due(["task"], remove=True)
    assert "removed" in result.lower()
    assert get_pending_items()[0][3] is None


def test_set_due_missing_date(tmp_life_dir):
    from life.core.item import add_task

    add_task("task")
    result = set_due(["task"], remove=False)
    assert "required" in result.lower()


def test_set_due_empty_args():
    result = set_due([])
    assert "required" in result.lower()


@pytest.mark.parametrize("tag", ["habit", "chore"])
def test_set_due_fails_on_non_task(tmp_life_dir, tag):
    from life.core.item import add_item

    add_item("item", tags=[tag])
    result = set_due(["2025-12-31", "item"])
    assert "cannot" in result.lower()


def test_set_due_no_match(tmp_life_dir):
    result = set_due(["2025-12-31", "nonexistent"])
    assert "No match" in result
