from life.lib.match import (
    complete,
    find_item,
    remove,
    toggle,
    uncomplete,
)


def test_complete_with_empty_string(tmp_life_dir):
    result = complete("")
    assert result is None


def test_uncomplete_with_empty_string(tmp_life_dir):
    result = uncomplete("")
    assert result is None


def test_toggle_with_empty_string(tmp_life_dir):
    result = toggle("")
    assert result is None


def test_find_item_with_empty_string(tmp_life_dir):
    result = find_item("")
    assert result is None


def test_remove_with_empty_string(tmp_life_dir):
    result = remove("")
    assert result is None


def test_find_item_uuid_prefix_too_short(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    iid = add_item("test")
    items = get_pending_items()
    from life.lib.match import _find_by_partial

    result = _find_by_partial(iid[:7], items)
    assert result is None


def test_complete_habit_multiple_times_same_day(tmp_life_dir):
    from life.core.item import add_item

    iid = add_item("habit", tags=["habit"])
    from life.core.repeat import check_repeat

    check_repeat(iid)
    check_repeat(iid)

    from life.core.item import get_pending_items

    items = get_pending_items()
    assert items[0][6] == 1


def test_toggle_multiple_times(tmp_life_dir):
    from life.core.item import add_task, get_pending_items

    add_task("task")
    toggle("task")
    toggle("task")

    items = get_pending_items()
    assert items[0][2] == 0


def test_remove_nonexistent_item(tmp_life_dir):
    result = remove("doesnotexist")
    assert result is None


def test_find_by_substring_partial_word(tmp_life_dir):
    from life.core.item import add_task

    add_task("implementation strategy")
    result = find_item("impl")
    assert result is not None
    assert "implementation" in result[1]


def test_find_by_substring_whole_word_match(tmp_life_dir):
    from life.core.item import add_task

    add_task("review authentication module")
    add_task("authenticate user request")

    result = find_item("authentication")
    assert result is not None
    assert "review" in result[1]


def test_complete_and_undo_same_day(tmp_life_dir):
    from life.core.item import add_task

    add_task("reversible")
    complete("reversible")

    uncompleted = uncomplete("reversible")
    assert uncompleted == "reversible"

    result = find_item("reversible")
    assert result is not None


def test_unicode_in_task_name(tmp_life_dir):
    from life.core.item import add_task

    add_task("Fix 🐛 bug")
    result = find_item("🐛")
    assert result is not None
    assert "🐛" in result[1]


def test_very_long_task_name(tmp_life_dir):
    from life.core.item import add_task

    long_name = "x" * 500
    add_task(long_name)
    result = find_item("x" * 100)
    assert result is not None
    assert long_name in result[1]
