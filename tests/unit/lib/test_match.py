from life.api import add_item, get_pending_items
from life.lib.match import _find_by_partial, find_item


def test_find_by_uuid_prefix(tmp_life_dir):
    item_id = add_item("test item")
    items = get_pending_items()
    result = _find_by_partial(item_id[:8], items)
    assert result is not None
    assert result.id == item_id


def test_find_by_substring(tmp_life_dir):
    add_item("write documentation")
    items = get_pending_items()
    result = _find_by_partial("document", items)
    assert result is not None
    assert "document" in result.content.lower()


def test_find_by_fuzzy_match(tmp_life_dir):
    add_item("meeting with team")
    items = get_pending_items()
    result = _find_by_partial("meeting", items)
    assert result is not None


def test_find_item_in_pending(tmp_life_dir):
    add_item("urgent review")
    result = find_item("review")
    assert result is not None
    assert "review" in result.content.lower()


def test_find_item_empty_pool(tmp_life_dir):
    result = find_item("nonexistent")
    assert result is None


def test_find_item_partial_uuid(tmp_life_dir):
    item_id = add_item("specific task")
    result = find_item(item_id[:8])
    assert result is not None
    assert result.id == item_id
