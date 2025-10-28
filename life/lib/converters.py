from datetime import date, datetime

from ..api.models import Item


def _row_to_item(row: tuple) -> Item:
    """
    Converts a raw database row into a clean Item object.
    This function is the single source of truth for handling the inconsistent
    date/time formats currently in the database.
    """

    # Handle 'due' date (can be str or numeric timestamp)
    due_val = row[3]
    due_date = None
    if isinstance(due_val, str) and due_val:
        due_date = date.fromisoformat(due_val.split("T")[0])
    elif isinstance(due_val, (int, float)):
        due_date = datetime.fromtimestamp(due_val).date()

    # Handle 'created' datetime (can be str or numeric timestamp)
    created_val = row[4]
    created_dt = datetime.min  # A safe default
    if isinstance(created_val, (int, float)):
        created_dt = datetime.fromtimestamp(created_val)
    elif isinstance(created_val, str) and created_val:
        created_dt = datetime.fromisoformat(created_val)

    # Handle 'completed' datetime (can be str or numeric timestamp)
    completed_val = row[5]
    completed_dt = None
    if isinstance(completed_val, str) and completed_val:
        try:
            completed_dt = datetime.fromisoformat(completed_val)
        except ValueError:
            # Handle cases where it might be just a date 'YYYY-MM-DD'
            completed_dt = datetime.combine(date.fromisoformat(completed_val), datetime.min.time())
    elif isinstance(completed_val, (int, float)):
        completed_dt = datetime.fromtimestamp(completed_val)

    return Item(
        id=row[0],
        content=row[1],
        focus=bool(row[2]),
        due=due_date,
        created=created_dt,
        completed=completed_dt,
        is_habit=bool(row[6]) if len(row) > 6 else False,
    )
