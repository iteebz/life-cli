import pytest

from life.lib.match import _find_by_partial, find_item


def test_find_by_partial_empty_pool():
    assert _find_by_partial("anything", []) is None


def test_find_uuid_prefix(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    iid = add_item("target")
    result = _find_by_partial(iid[:8], get_pending_items())
    assert result and result[0] == iid


def test_find_substring(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("fix broken widget")
    result = _find_by_partial("broken", get_pending_items())
    assert result and "broken" in result[1]


def test_find_substring_case_insensitive(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("Fix Broken Widget")
    result = _find_by_partial("BROKEN", get_pending_items())
    assert result and "broken" in result[1].lower()


def test_find_fuzzy_match(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("refactor authentication module")
    result = _find_by_partial("refactor authen", get_pending_items())
    assert result and "refactor" in result[1].lower()


def test_find_no_match(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("something else")
    assert _find_by_partial("completely different", get_pending_items()) is None


def test_find_uuid_prefix_too_short(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    iid = add_item("test")
    assert _find_by_partial(iid[:7], get_pending_items()) is None


def test_find_multiple_items(tmp_life_dir):
    from life.core.item import add_item, get_pending_items

    add_item("apple")
    add_item("apricot")
    result = _find_by_partial("ap", get_pending_items())
    assert result and result[1] in ("apple", "apricot")


def test_find_item_from_pending(tmp_life_dir):
    from life.core.item import add_item

    add_item("pending task")
    result = find_item("pending")
    assert result and "pending" in result[1]


def test_find_item_excludes_completed(tmp_life_dir):
    from life.core.item import add_item, complete_item

    iid = add_item("done task")
    complete_item(iid)
    assert find_item("done") is None


@pytest.mark.parametrize(
    "content",
    [
        "implementation strategy",
        "review authentication module",
        "Fix 🐛 bug",
    ],
)
def test_find_unicode_and_long(tmp_life_dir, content):
    from life.core.item import add_task

    add_task(content)
    result = find_item(content[:5])
    assert result and content in result[1]


def test_find_very_long_name(tmp_life_dir):
    from life.core.item import add_task

    long_name = "x" * 500
    add_task(long_name)
    result = find_item("x" * 100)
    assert result and long_name in result[1]
