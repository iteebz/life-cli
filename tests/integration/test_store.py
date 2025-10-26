from life.core.item import (
    add_item,
    complete_item,
    delete_item,
    get_pending_items,
    is_repeating,
    toggle_focus,
    update_item,
)
from life.core.repeat import check_repeat
from life.core.tag import add_tag, get_items_by_tag, get_tags
from life.lib.sqlite import init_db


def id_(row):
    return row[0]


def content(row):
    return row[1]


def focus(row):
    return row[2]


def due(row):
    return row[3]


def check_count(row):
    return row[6]


def test_db_init(tmp_life_dir):
    init_db()
    assert (tmp_life_dir / "store.db").exists()


def test_add(tmp_life_dir):
    add_item("task")
    items = get_pending_items()
    assert len(items) == 1
    assert content(items[0]) == "task"


def test_focus_on_add(tmp_life_dir):
    add_item("urgent", focus=True)
    items = get_pending_items()
    assert focus(items[0]) == 1


def test_due_on_add(tmp_life_dir):
    add_item("deadline", due="2025-12-31")
    items = get_pending_items()
    assert due(items[0]) == "2025-12-31"


def test_complete(tmp_life_dir):
    add_item("task")
    items = get_pending_items()
    complete_item(id_(items[0]))
    assert len(get_pending_items()) == 0


def test_focus_toggle(tmp_life_dir):
    add_item("task")
    items = get_pending_items()
    iid = id_(items[0])
    new_state = toggle_focus(iid, 0)
    assert new_state == 1
    items = get_pending_items()
    assert focus(items[0]) == 1


def test_update_content(tmp_life_dir):
    iid = add_item("old")
    update_item(iid, content="new")
    items = get_pending_items()
    assert content(items[0]) == "new"


def test_update_due(tmp_life_dir):
    iid = add_item("task")
    update_item(iid, due="2025-06-01")
    items = get_pending_items()
    assert due(items[0]) == "2025-06-01"


def test_delete(tmp_life_dir):
    add_item("a")
    add_item("b")
    items = get_pending_items()
    delete_item(id_(items[0]))
    assert len(get_pending_items()) == 1


def test_tags_on_add(tmp_life_dir):
    add_item("task", tags=["work", "urgent"])
    items = get_pending_items()
    tags = get_tags(id_(items[0]))
    assert "work" in tags
    assert "urgent" in tags


def test_tag_add(tmp_life_dir):
    iid = add_item("task")
    add_tag(iid, "priority")
    tags = get_tags(iid)
    assert "priority" in tags


def test_tag_duplicate_ignored(tmp_life_dir):
    iid = add_item("task")
    add_tag(iid, "work")
    add_tag(iid, "work")
    tags = get_tags(iid)
    assert len(tags) == 1


def test_tag_case_normalized(tmp_life_dir):
    iid = add_item("task")
    add_tag(iid, "URGENT")
    tags = get_tags(iid)
    assert "urgent" in tags


def test_get_by_tag(tmp_life_dir):
    iid = add_item("tagged")
    add_item("untagged")
    add_tag(iid, "focus")
    tagged = get_items_by_tag("focus")
    assert len(tagged) == 1
    assert id_(tagged[0]) == iid


def test_sort_by_focus(tmp_life_dir):
    add_item("low")
    add_item("high", focus=True)
    items = get_pending_items()
    assert focus(items[0]) == 1


def test_sort_by_due(tmp_life_dir):
    add_item("later", due="2025-12-31")
    add_item("sooner", due="2025-01-01")
    items = get_pending_items()
    assert content(items[0]) == "sooner"


def test_focus_trumps_due(tmp_life_dir):
    add_item("low", due="2025-01-01")
    add_item("high", focus=True, due="2025-12-31")
    items = get_pending_items()
    assert focus(items[0]) == 1


def test_repeat_habit(tmp_life_dir):
    add_item("habit", tags=["habit"])
    items = get_pending_items()
    assert is_repeating(id_(items[0]))


def test_repeat_chore(tmp_life_dir):
    add_item("chore", tags=["chore"])
    items = get_pending_items()
    assert is_repeating(id_(items[0]))


def test_repeat_not_task(tmp_life_dir):
    add_item("task")
    items = get_pending_items()
    assert not is_repeating(id_(items[0]))


def test_check_repeat(tmp_life_dir):
    iid = add_item("habit", tags=["habit"])
    check_repeat(iid)
    items = get_pending_items()
    assert check_count(items[0]) == 1


def test_check_repeat_once_per_day(tmp_life_dir):
    iid = add_item("habit", tags=["habit"])
    check_repeat(iid)
    check_repeat(iid)
    items = get_pending_items()
    assert check_count(items[0]) == 1


def test_check_repeat_to_completion(tmp_life_dir):
    from datetime import date, timedelta

    iid = add_item("5x", tags=["habit"], target_count=5)
    for i in range(5):
        check_date = (date.today() - timedelta(days=5 - i)).isoformat()
        check_repeat(iid, check_date)
    assert len(get_pending_items()) == 0


def test_delete_removes_tags(tmp_life_dir):
    iid = add_item("task")
    add_tag(iid, "focus")
    delete_item(iid)
    assert len(get_items_by_tag("focus")) == 0
