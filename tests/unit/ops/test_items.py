from life.api import add_item
from life.ops import manage_tag, set_due


def test_set_due_via_ops(tmp_life_dir):
    item_id = add_item("task")
    result = set_due([str(item_id)], remove=False)
    assert "Due date required" in result or "No match" not in result


def test_set_due_with_date(tmp_life_dir):
    item_id = add_item("task")
    result = set_due(["2025-12-25", str(item_id)])
    assert "Due" in result


def test_manage_tag_add(tmp_life_dir):
    item_id = add_item("task")
    result = manage_tag("urgent", str(item_id))
    assert "Tagged" in result


def test_manage_tag_remove(tmp_life_dir):
    item_id = add_item("task", tags=["urgent"])
    result = manage_tag("urgent", str(item_id), remove=True)
    assert "Untagged" in result


def test_manage_tag_list(tmp_life_dir):
    add_item("task 1", tags=["work"])
    add_item("task 2", tags=["work"])
    result = manage_tag("work")
    assert "WORK" in result
