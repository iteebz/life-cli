from life.lib.match import (
    _find_by_partial,
    complete,
    find_item,
    remove,
    set_due,
    toggle,
    uncomplete,
    update,
)


def test_find_by_partial_empty_pool():
    result = _find_by_partial("anything", [])
    assert result is None


def test_find_by_uuid_prefix(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    iid = add_item("target")
    items = get_pending_items()
    result = _find_by_partial(iid[:8], items)
    assert result is not None
    assert result[0] == iid


def test_find_by_substring(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("fix broken widget")
    items = get_pending_items()
    result = _find_by_partial("broken", items)
    assert result is not None
    assert "broken" in result[1]


def test_find_by_substring_case_insensitive(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("Fix Broken Widget")
    items = get_pending_items()
    result = _find_by_partial("BROKEN", items)
    assert result is not None


def test_find_by_fuzzy_match(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("refactor authentication module")
    items = get_pending_items()
    result = _find_by_partial("refactor authen", items)
    assert result is not None
    assert "refactor" in result[1].lower()


def test_find_no_match(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("something else")
    items = get_pending_items()
    result = _find_by_partial("completely different", items)
    assert result is None


def test_find_item_pending(tmp_life_dir):
    from life.core.item import add_item

    add_item("pending task")
    result = find_item("pending")
    assert result is not None
    assert "pending" in result[1]


def test_find_item_completed_not_found(tmp_life_dir):
    from life.core.item import add_item, complete_item

    iid = add_item("done task")
    complete_item(iid)
    result = find_item("done")
    assert result is None


def test_complete_task(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("complete me")
    result = complete("complete")
    assert result == "complete me"
    assert len(get_pending_items()) == 0


def test_complete_habit_checks(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("meditate", tags=["habit"])
    result = complete("meditate")
    assert result == "meditate"
    items = get_pending_items()
    assert len(items) == 1
    assert items[0][6] == 1


def test_complete_nonexistent():
    result = complete("nonexistent")
    assert result is None


def test_uncomplete_from_today(tmp_life_dir):
    from life.core.item import add_item, complete_item

    iid = add_item("undo me")
    complete_item(iid)
    result = uncomplete("undo")
    assert result == "undo me"


def test_uncomplete_not_today(tmp_life_dir):
    from datetime import date, timedelta

    from life.core.item import add_item

    iid = add_item("old")
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    import sqlite3

    from life.lib.sqlite import DB_PATH

    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE items SET completed = ? WHERE id = ?", (yesterday, iid))
    conn.commit()
    conn.close()

    result = uncomplete("old")
    assert result is None


def test_toggle_focus_off(tmp_life_dir):
    from life.core.item import add_item

    add_item("focused", focus=True)
    result = toggle("focused")
    assert result is not None
    assert result[0] == "Unfocused"


def test_toggle_focus_on(tmp_life_dir):
    from life.core.item import add_item

    add_item("unfocused")
    result = toggle("unfocused")
    assert result is not None
    assert result[0] == "Focused"


def test_toggle_no_match():
    result = toggle("nonexistent")
    assert result is None


def test_update_content(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("old content")
    result = update("old", content="new content")
    assert result == "new content"
    items = get_pending_items()
    assert items[0][1] == "new content"


def test_update_due(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("task")
    result = update("task", due="2025-12-31")
    assert result == "task"
    items = get_pending_items()
    assert items[0][3] == "2025-12-31"


def test_update_focus(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("task")
    result = update("task", focus=True)
    assert result == "task"
    items = get_pending_items()
    assert items[0][2] == 1


def test_update_no_match():
    result = update("nonexistent", content="new")
    assert result is None


def test_remove_item(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("delete me")
    result = remove("delete")
    assert result == "delete me"
    assert len(get_pending_items()) == 0


def test_remove_no_match():
    result = remove("nonexistent")
    assert result is None


def test_set_due_with_date(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("deadline task")
    result = set_due(["2025-12-31", "deadline"])
    assert "2025-12-31" in result
    items = get_pending_items()
    assert items[0][3] == "2025-12-31"


def test_set_due_remove(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("task", due="2025-12-31")
    result = set_due(["task"], remove=True)
    assert "removed" in result.lower()
    items = get_pending_items()
    assert items[0][3] is None


def test_set_due_missing_date(tmp_life_dir):
    from life.core.item import add_task

    add_task("task")
    result = set_due(["task"], remove=False)
    assert "required" in result.lower()


def test_set_due_empty_args():
    result = set_due([])
    assert "required" in result.lower()


def test_set_due_no_match(tmp_life_dir):
    result = set_due(["2025-12-31", "nonexistent"])
    assert "No match" in result


def test_find_by_partial_multiple_items_returns_first(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("apple")
    add_item("apricot")
    items = get_pending_items()
    result = _find_by_partial("ap", items)
    assert result is not None
    assert result[1] in ("apple", "apricot")


def test_remove_duplicate_lifo(tmp_life_dir):
    import time

    from life.core.item import add_item, get_pending_items

    for _ in range(3):
        add_item("remove me")
        time.sleep(0.1)

    initial_count = len(get_pending_items())
    assert initial_count >= 3

    for i in range(3):
        result = remove("remove me")
        assert result == "remove me"
        remaining_count = len(get_pending_items())
        assert remaining_count == initial_count - (i + 1)


def test_remove_completed_task_today(tmp_life_dir):
    from life.core.item import add_item, complete_item, get_pending_items, get_today_completed

    iid = add_item("completed task")
    complete_item(iid)

    assert len(get_pending_items()) == 0
    assert len(get_today_completed()) == 1

    result = remove("completed")
    assert result == "completed task"
    assert len(get_today_completed()) == 0


def test_remove_prefers_pending_over_completed(tmp_life_dir):
    from life.core.item import add_item, complete_item, get_pending_items, get_today_completed

    iid_completed = add_item("match")
    complete_item(iid_completed)

    add_item("match")

    assert len(get_pending_items()) == 1
    assert len(get_today_completed()) == 1

    result = remove("match")
    assert result == "match"
    assert len(get_pending_items()) == 0
    assert len(get_today_completed()) == 1


def test_remove_habit_pending(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("meditate", tags=["habit"])

    result = remove("meditate")
    assert result == "meditate"
    assert len(get_pending_items()) == 0


def test_remove_chore_pending(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("wash dishes", tags=["chore"])

    result = remove("wash")
    assert result == "wash dishes"
    assert len(get_pending_items()) == 0
