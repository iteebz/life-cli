from life.core.item import (
    add_chore,
    add_habit,
    add_task,
    get_pending_items,
    get_today_completed,
    is_repeating,
)
from life.core.tag import add_tag, manage_tag
from life.lib.ops import (
    complete,
    edit_item,
    remove,
    set_due,
    toggle,
    uncomplete,
)


def test_task_add_basic(tmp_life_dir):
    result = add_task("build feature")
    assert "build feature" in result


def test_task_add_with_focus(tmp_life_dir):
    result = add_task("urgent", focus=True)
    items = get_pending_items()
    assert items[0][2] == 1
    assert "urgent" in result


def test_task_add_with_due(tmp_life_dir):
    add_task("deadline", due="2025-12-31")
    items = get_pending_items()
    assert items[0][3] == "2025-12-31"


def test_task_add_with_tags(tmp_life_dir):
    add_task("tagged task", tags=["work", "urgent"])
    items = get_pending_items()
    from life.core.tag import get_tags

    tags = get_tags(items[0][0])
    assert "work" in tags
    assert "urgent" in tags


def test_task_add_done_immediately(tmp_life_dir):
    add_task("quick task", done=True)
    assert len(get_pending_items()) == 0
    assert len(get_today_completed()) == 1


def test_task_complete_transitions_state(tmp_life_dir):
    add_task("do this")
    complete("do this")
    assert len(get_pending_items()) == 0
    assert len(get_today_completed()) == 1


def test_habit_add(tmp_life_dir):
    result = add_habit("meditate")
    items = get_pending_items()
    assert items[0][1] == "meditate"
    assert is_repeating(items[0][0])
    assert "meditate" in result


def test_habit_check(tmp_life_dir):
    add_habit("exercise")
    complete("exercise")
    items = get_pending_items()
    assert items[0][6] == 1


def test_chore_add(tmp_life_dir):
    result = add_chore("dishes")
    items = get_pending_items()
    assert items[0][1] == "dishes"
    assert is_repeating(items[0][0])
    assert "dishes" in result


def test_focus_toggle_workflow(tmp_life_dir):
    add_task("less important")
    add_task("more important")
    items = get_pending_items()
    assert items[0][2] == 0

    toggle("more important")
    items = get_pending_items()
    assert items[0][2] == 1
    assert items[0][1] == "more important"


def test_tag_add_to_item(tmp_life_dir):
    from life.core.item import add_item
    from life.core.tag import get_tags

    iid = add_item("task")
    add_tag(iid, "priority")
    tags = get_tags(iid)
    assert "priority" in tags


def test_tag_manage_add(tmp_life_dir):
    add_task("cleanup")
    result = manage_tag("urgent", "cleanup")
    assert "cleanup" in result
    assert "urgent" in result.lower()


def test_tag_manage_remove(tmp_life_dir):
    from life.core.item import add_item

    iid = add_item("task")
    add_tag(iid, "work")
    result = manage_tag("work", "task", remove=True)
    assert "Untagged" in result


def test_tag_manage_view(tmp_life_dir):
    from life.core.item import add_item

    iid = add_item("tagged")
    add_tag(iid, "focus")
    result = manage_tag("focus")
    assert "FOCUS" in result
    assert "tagged" in result


def test_tag_manage_no_items(tmp_life_dir):
    result = manage_tag("nosuch")
    assert "No items" in result


def test_edit_item_content(tmp_life_dir):
    add_task("old title")
    result = edit_item("new title", "old")
    assert "Updated" in result
    assert "new title" in result
    items = get_pending_items()
    assert items[0][1] == "new title"


def test_due_set_and_clear(tmp_life_dir):
    add_task("deadline work")
    set_due(["2025-12-31", "deadline"])
    items = get_pending_items()
    assert items[0][3] == "2025-12-31"

    set_due(["deadline"], remove=True)
    items = get_pending_items()
    assert items[0][3] is None


def test_remove_item_deletes(tmp_life_dir):
    add_task("cleanup")
    result = remove("cleanup")
    assert "cleanup" in result
    assert len(get_pending_items()) == 0


def test_undo_completion(tmp_life_dir):
    add_task("undo me")
    complete("undo")
    assert len(get_pending_items()) == 0

    uncomplete("undo")
    assert len(get_pending_items()) == 1


def test_multiple_items_fuzzy_match_first(tmp_life_dir):
    add_task("apple pie")
    add_task("application")
    get_pending_items()

    result = complete("app")
    assert result in ("apple pie", "application")
    assert len(get_pending_items()) == 1


def test_focus_clears_on_complete(tmp_life_dir):
    add_task("focused task", focus=True)
    complete("focused")
    items = get_pending_items()
    assert len(items) == 0


def test_task_sorting_focus_first(tmp_life_dir):
    add_task("low")
    add_task("high", focus=True)
    items = get_pending_items()
    assert items[0][2] == 1


def test_task_sorting_due_within_focus(tmp_life_dir):
    add_task("later", focus=True, due="2025-12-31")
    add_task("sooner", focus=True, due="2025-01-01")
    items = get_pending_items()
    assert items[0][1] == "sooner"


def test_habit_target_completion(tmp_life_dir):
    from life.core.item import add_item

    iid = add_item("5check", tags=["habit"], target_count=5)
    from datetime import date, timedelta

    from life.core.repeat import check_repeat

    for i in range(5):
        check_date = (date.today() - timedelta(days=5 - i)).isoformat()
        check_repeat(iid, check_date)

    assert len(get_pending_items()) == 0
    completed = get_today_completed()
    assert any(iid in str(c) for c in completed)


def test_habit_max_three_target(tmp_life_dir):
    from datetime import date, timedelta

    from life.core.item import add_item
    from life.core.repeat import check_repeat

    iid = add_item("strength", tags=["habit"], target_count=3)

    for i in range(3):
        check_date = (date.today() - timedelta(days=3 - i)).isoformat()
        check_repeat(iid, check_date)

    items = get_pending_items()
    assert len(items) == 0
