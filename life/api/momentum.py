import datetime
from datetime import timedelta

from .. import db
from ..lib import clock
from .models import Weekly


def _calculate_total_possible(active_items_data, week_start_date, week_end_date):
    total_possible = 0
    for _item_id, created_value, is_repeat in active_items_data:
        if isinstance(created_value, str):
            try:
                created_date = datetime.date.fromisoformat(created_value)
            except ValueError:
                created_date = datetime.date.fromtimestamp(float(created_value))
        elif isinstance(created_value, (int, float)):
            created_date = datetime.date.fromtimestamp(created_value)
        elif isinstance(created_value, datetime.datetime):
            created_date = created_value.date()
        else:
            created_date = datetime.date.min

        if created_date > week_end_date:
            continue

        if week_start_date <= created_date <= week_end_date:
            if created_date == week_start_date:
                days_active = (week_end_date - created_date).days + 1
            else:
                # Treat mid-week creations as a single-day commitment so new habits
                # are not penalized before they settle into a cadence.
                days_active = 1
        else:
            active_start = max(created_date, week_start_date)
            if active_start > week_end_date:
                continue
            days_active = (week_end_date - active_start).days + 1

        per_day_target = 1 if is_repeat else 1  # Always 1 for habits/chores as per new rule
        total_possible += days_active * per_day_target

    return total_possible


def weekly_momentum():
    """Get weekly totals: this week, last week, prior week"""
    today = clock.today()

    this_week_start = today - timedelta(days=6)
    this_week_end = today

    last_week_start = today - timedelta(days=13)
    last_week_end = today - timedelta(days=7)

    prior_week_start = today - timedelta(days=20)
    prior_week_end = today - timedelta(days=14)

    weeks = {}

    with db.get_db() as conn:
        for week_name, start_date, end_date in [
            ("this_week", this_week_start, this_week_end),
            ("last_week", last_week_start, last_week_end),
            ("prior_week", prior_week_start, prior_week_end),
        ]:
            start_str = start_date.isoformat()
            end_str = end_date.isoformat()
            cursor = conn.execute(
                """
                SELECT COUNT(*)
                FROM items
                WHERE completed >= ?
                AND completed <= ?
                AND completed IS NOT NULL
                AND COALESCE(is_repeat, 0) = 0
            """,
                (start_str, end_str),
            )
            tasks = cursor.fetchone()[0]

            cursor = conn.execute(
                """
                SELECT COUNT(*)
                FROM checks c
                INNER JOIN tags it ON c.item_id = it.item_id
                WHERE it.tag = 'habit'
                AND DATE(
                    CASE
                        WHEN typeof(c.check_date) IN ('integer','real')
                            THEN datetime(c.check_date, 'unixepoch')
                        ELSE c.check_date
                    END
                ) >= ?
                AND DATE(
                    CASE
                        WHEN typeof(c.check_date) IN ('integer','real')
                            THEN datetime(c.check_date, 'unixepoch')
                        ELSE c.check_date
                    END
                ) <= ?
            """,
                (start_str, end_str),
            )
            habits = cursor.fetchone()[0]

            cursor = conn.execute(
                """
                SELECT COUNT(*)
                FROM checks c
                INNER JOIN tags it ON c.item_id = it.item_id
                AND DATE(
                    CASE
                        WHEN typeof(c.check_date) IN ('integer','real')
                            THEN datetime(c.check_date, 'unixepoch')
                        ELSE c.check_date
                    END
                ) >= ?
                AND DATE(
                    CASE
                        WHEN typeof(c.check_date) IN ('integer','real')
                            THEN datetime(c.check_date, 'unixepoch')
                        ELSE c.check_date
                    END
                ) <= ?
            """,
                (start_str, end_str),
            )
            chores = cursor.fetchone()[0]

            # Get total active tasks for the week
            cursor = conn.execute(
                """
                SELECT COUNT(*)
                FROM items
                WHERE (
                    DATE(
                        CASE
                            WHEN typeof(created) IN ('integer','real')
                                THEN datetime(created, 'unixepoch')
                            ELSE created
                        END
                    ) <= ?
                    OR (completed >= ? AND completed <= ?)
                )
                AND COALESCE(is_repeat, 0) = 0
                """,
                (end_str, start_str, end_str),
            )
            tasks_total = cursor.fetchone()[0]

            # Get all habits active during the week
            cursor = conn.execute(
                """
                SELECT DISTINCT
                    i.id,
                    i.created,
                    i.is_repeat
                FROM items i
                INNER JOIN tags it ON i.id = it.item_id
                WHERE it.tag = 'habit'
                """
            )
            active_habits_data = cursor.fetchall()

            habits_total_possible = _calculate_total_possible(
                active_habits_data,
                datetime.date.fromisoformat(start_str),
                datetime.date.fromisoformat(end_str),
            )

            # Get all chores active during the week
            cursor = conn.execute(
                """
                SELECT DISTINCT
                    i.id,
                    i.created,
                    i.is_repeat
                FROM items i
                INNER JOIN tags it ON i.id = it.item_id
                WHERE it.tag = 'chore'
                """,
            )
            active_chores_data = cursor.fetchall()

            chores_total_possible = _calculate_total_possible(
                active_chores_data,
                datetime.date.fromisoformat(start_str),
                datetime.date.fromisoformat(end_str),
            )

            weeks[week_name] = Weekly(
                tasks_completed=tasks,
                tasks_total=tasks_total,
                habits_completed=habits,
                habits_total=habits_total_possible,
                chores_completed=chores,
                chores_total=chores_total_possible,
            )

    return weeks
