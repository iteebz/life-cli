from life.api import add_item, add_tag, delete_item, get_items_by_tag, get_tags, remove_tag
from life.api.models import Item


def id_(item: Item):
    return item.id


def test_add_tag_on_creation(tmp_life_dir):
    item_id = add_item("tagged item", tags=["urgent"])
    tags = get_tags(item_id)
    assert "urgent" in tags


def test_add_tag_after_creation(tmp_life_dir):
    item_id = add_item("untagged item")
    add_tag(item_id, "important")
    tags = get_tags(item_id)
    assert "important" in tags


def test_get_tags(tmp_life_dir):
    item_id = add_item("multi-tag item", tags=["work", "urgent"])
    tags = get_tags(item_id)
    assert "work" in tags
    assert "urgent" in tags


def test_get_tags_empty(tmp_life_dir):
    item_id = add_item("untagged item")
    tags = get_tags(item_id)
    assert len(tags) == 0


def test_remove_tag(tmp_life_dir):
    item_id = add_item("item", tags=["important"])
    remove_tag(item_id, "important")
    tags = get_tags(item_id)
    assert "important" not in tags


def test_remove_nonexistent_tag(tmp_life_dir):
    item_id = add_item("item", tags=["existing"])
    remove_tag(item_id, "nonexistent")
    tags = get_tags(item_id)
    assert "existing" in tags


def test_get_items_by_tag(tmp_life_dir):
    item1_id = add_item("task 1", tags=["work"])
    item2_id = add_item("task 2", tags=["work"])
    add_item("task 3", tags=["personal"])

    work_items = get_items_by_tag("work")
    assert len(work_items) >= 2
    assert any(item.id == item1_id for item in work_items)
    assert any(item.id == item2_id for item in work_items)


def test_get_items_by_nonexistent_tag(tmp_life_dir):
    add_item("task 1", tags=["work"])
    items = get_items_by_tag("nonexistent")
    assert len(items) == 0


def test_tag_case_normalization(tmp_life_dir):
    item_id = add_item("item", tags=["URGENT"])
    tags = get_tags(item_id)
    assert "urgent" in tags


def test_tags_on_add(tmp_life_dir):
    item_id = add_item("task", tags=["work", "urgent"])
    tags = get_tags(item_id)
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


def test_delete_removes_tags(tmp_life_dir):
    iid = add_item("task")
    add_tag(iid, "focus")
    delete_item(iid)
    assert len(get_items_by_tag("focus")) == 0
