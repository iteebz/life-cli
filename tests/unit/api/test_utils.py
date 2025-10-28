from datetime import date, datetime

from life.api.utils import _row_to_item


def test_row_to_item_handles_empty_due_date():
    # Simulate a row from the database where 'due' is an empty string
    row_with_empty_due = (
        "test-id",
        "test content",
        0,  # focus
        "",  # empty string for due date
        datetime.now().timestamp(),  # created
        None,  # completed
        0,  # is_repeat
    )
    item = _row_to_item(row_with_empty_due)
    assert item.due is None


def test_row_to_item_handles_valid_due_date():
    # Simulate a row with a valid due date
    row_with_valid_due = (
        "test-id-2",
        "test content 2",
        0,  # focus
        "2025-12-31",  # valid ISO format string for due date
        datetime.now().timestamp(),  # created
        None,  # completed
        0,  # is_repeat
    )
    item = _row_to_item(row_with_valid_due)
    assert item.due == date(2025, 12, 31)


def test_row_to_item_handles_none_due_date():
    # Simulate a row with None for due date
    row_with_none_due = (
        "test-id-3",
        "test content 3",
        0,  # focus
        None,  # None for due date
        datetime.now().timestamp(),  # created
        None,  # completed
        0,  # is_repeat
    )
    item = _row_to_item(row_with_none_due)
    assert item.due is None
