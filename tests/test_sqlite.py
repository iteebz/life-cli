from life.config import get_context, set_context
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


def test_init_creates_db(tmp_life_dir):
    init_db()
    assert (tmp_life_dir / "store.db").exists()


def test_add_item(tmp_life_dir):
    add_item("test item")
    items = get_pending_items()
    assert len(items) == 1
    assert items[0][1] == "test item"


def test_add_item_with_focus(tmp_life_dir):
    add_item("important", focus=True)
    items = get_pending_items()
    assert items[0][2] == 1


def test_add_item_with_due(tmp_life_dir):
    add_item("deadline", due="2025-12-31")
    items = get_pending_items()
    assert items[0][3] == "2025-12-31"


def test_complete_item(tmp_life_dir):
    add_item("item")
    items = get_pending_items()
    complete_item(items[0][0])
    assert len(get_pending_items()) == 0


def test_completed_item_excluded_from_pending(tmp_life_dir):
    item_a = add_item("a")
    item_b = add_item("b")
    complete_item(item_a)
    remaining = get_pending_items()
    assert len(remaining) == 1
    assert remaining[0][0] == item_b


def test_toggle_focus(tmp_life_dir):
    add_item("item")
    items = get_pending_items()
    item_id, _, focus, *_ = items[0]
    assert focus == 0
    new_focus = toggle_focus(item_id, focus)
    assert new_focus == 1


def test_toggle_focus_twice(tmp_life_dir):
    add_item("item")
    items = get_pending_items()
    item_id = items[0][0]
    toggle_focus(item_id, 0)
    toggle_focus(item_id, 1)
    items = get_pending_items()
    assert items[0][2] == 0


def test_update_content(tmp_life_dir):
    add_item("old")
    items = get_pending_items()
    update_item(items[0][0], content="new")
    items = get_pending_items()
    assert items[0][1] == "new"


def test_update_due(tmp_life_dir):
    add_item("item")
    items = get_pending_items()
    update_item(items[0][0], due="2025-12-31")
    items = get_pending_items()
    assert items[0][3] == "2025-12-31"


def test_update_multiple_fields(tmp_life_dir):
    add_item("old")
    items = get_pending_items()
    item_id = items[0][0]
    update_item(item_id, content="new", due="2025-06-01", focus=True)
    items = get_pending_items()
    assert items[0][1] == "new"
    assert items[0][2] == 1
    assert items[0][3] == "2025-06-01"


def test_add_habit(tmp_life_dir):
    add_item("meditate", tags=["habit"])
    items = get_pending_items()
    tags = get_tags(items[0][0])
    assert "habit" in tags


def test_add_chore(tmp_life_dir):
    add_item("dishes", tags=["chore"])
    items = get_pending_items()
    tags = get_tags(items[0][0])
    assert "chore" in tags


def test_categories_mix(tmp_life_dir):
    add_item("task")
    add_item("habit", tags=["habit"])
    add_item("chore", tags=["chore"])
    items = get_pending_items()
    assert len(items) == 3
    tags_sets = [set(get_tags(i[0])) for i in items]
    assert any("habit" in t for t in tags_sets)
    assert any("chore" in t for t in tags_sets)


def test_check_habit(tmp_life_dir):
    add_item("hydrate", tags=["habit"])
    items = get_pending_items()
    check_repeat(items[0][0])
    items = get_pending_items()
    tags = get_tags(items[0][0])
    assert "habit" in tags


def test_check_counts_to_completion(tmp_life_dir):
    from datetime import date, timedelta

    add_item("5x", tags=["habit"], target_count=5)
    item_id = get_pending_items()[0][0]
    for i in range(5):
        check_date = (date.today() - timedelta(days=5 - i)).isoformat()
        check_repeat(item_id, check_date)
    assert len(get_pending_items()) == 0


def test_check_duplicate_same_day_ignored(tmp_life_dir):
    add_item("check", tags=["habit"])
    item_id = get_pending_items()[0][0]
    check_repeat(item_id)
    check_repeat(item_id)
    assert get_pending_items()[0][6] == 1


def test_add_tag(tmp_life_dir):
    add_item("item")
    item_id = get_pending_items()[0][0]
    add_tag(item_id, "urgent")
    tags = get_tags(item_id)
    assert "urgent" in tags


def test_duplicate_tag_ignored(tmp_life_dir):
    add_item("item")
    item_id = get_pending_items()[0][0]
    add_tag(item_id, "work")
    add_tag(item_id, "work")
    tags = get_tags(item_id)
    assert len(tags) == 1


def test_tag_case_normalized(tmp_life_dir):
    add_item("item")
    item_id = get_pending_items()[0][0]
    add_tag(item_id, "URGENT")
    tags = get_tags(item_id)
    assert "urgent" in tags


def test_get_items_by_tag(tmp_life_dir):
    item_a = add_item("a")
    add_item("b")
    add_tag(item_a, "focus")
    tagged = get_items_by_tag("focus")
    assert len(tagged) == 1
    assert tagged[0][0] == item_a


def test_context_lifecycle(tmp_life_dir):
    set_context("Wedding: 30 days")
    ctx = get_context()
    assert ctx == "Wedding: 30 days"
    assert (tmp_life_dir / "config.yaml").exists()


def test_delete_item(tmp_life_dir):
    add_item("a")
    add_item("b")
    item_id = get_pending_items()[0][0]
    delete_item(item_id)
    assert len(get_pending_items()) == 1


def test_delete_removes_tags(tmp_life_dir):
    add_item("a")
    item_id = get_pending_items()[0][0]
    add_tag(item_id, "focus")
    delete_item(item_id)
    assert len(get_items_by_tag("focus")) == 0


def test_pending_ordered_by_focus(tmp_life_dir):
    add_item("b")
    add_item("a", focus=True)
    items = get_pending_items()
    assert items[0][1] == "a"
    assert items[0][2] == 1


def test_pending_ordered_by_due(tmp_life_dir):
    add_item("later", due="2025-12-31")
    add_item("sooner", due="2025-01-01")
    items = get_pending_items()
    assert items[0][1] == "sooner"


def test_focus_trumps_due(tmp_life_dir):
    add_item("focus", focus=True, due="2025-12-31")
    add_item("due_soon", due="2025-01-01")
    items = get_pending_items()
    assert items[0][1] == "focus"


def test_is_repeating_habit(tmp_life_dir):
    add_item("habit", tags=["habit"])
    item_id = get_pending_items()[0][0]
    assert is_repeating(item_id)


def test_is_repeating_chore(tmp_life_dir):
    add_item("chore", tags=["chore"])
    item_id = get_pending_items()[0][0]
    assert is_repeating(item_id)


def test_is_not_repeating_task(tmp_life_dir):
    add_item("task")
    item_id = get_pending_items()[0][0]
    assert not is_repeating(item_id)


def test_is_not_repeating_with_custom_tags(tmp_life_dir):
    add_item("item", tags=["work", "urgent"])
    item_id = get_pending_items()[0][0]
    assert not is_repeating(item_id)
