from dataclasses import dataclass
from datetime import date, datetime, timedelta
from statistics import median

from .models import Task
from .tasks import count_overdue_resets

DISCOMFORT_TAGS = {"finance", "legal", "jaynice"}


@dataclass(frozen=True)
class FeedbackSnapshot:
    admin_closed: int
    admin_created: int
    jaynice_done: int
    jaynice_created: int
    avoidance_half_life_days: int
    overdue_resets: int
    flags: list[str]


def _in_window(ts: datetime | None, start: date, end: date) -> bool:
    if ts is None:
        return False
    day = ts.date()
    return start <= day <= end


def _format_ratio(done: int, created: int) -> str:
    if created == 0:
        return "n/a"
    return f"{done / created:.0%}"


def build_feedback_snapshot(
    *,
    all_tasks: list[Task],
    pending_tasks: list[Task],
    today: date,
    window_days: int = 7,
) -> FeedbackSnapshot:
    window_start = today - timedelta(days=window_days - 1)
    overdue_resets = count_overdue_resets(window_start.isoformat(), today.isoformat())

    admin_created = sum(
        1
        for t in all_tasks
        if t.due_date and window_start <= t.created.date() <= today and t.due_date < today
    )
    admin_closed = sum(
        1
        for t in all_tasks
        if t.due_date
        and _in_window(t.completed_at, window_start, today)
        and t.completed_at is not None
        and t.due_date < t.completed_at.date()
    )

    jaynice_created = sum(
        1
        for t in all_tasks
        if "jaynice" in (t.tags or []) and window_start <= t.created.date() <= today
    )
    jaynice_done = sum(
        1
        for t in all_tasks
        if "jaynice" in (t.tags or []) and _in_window(t.completed_at, window_start, today)
    )

    discomfort_open_ages = [
        (today - t.created.date()).days
        for t in pending_tasks
        if set(t.tags or []).intersection(DISCOMFORT_TAGS)
    ]
    avoidance_half_life_days = int(median(discomfort_open_ages)) if discomfort_open_ages else 0

    flags: list[str] = []
    if jaynice_created and (jaynice_done / jaynice_created) < 0.5:
        flags.append("relationship_escalation")
    if discomfort_open_ages and max(discomfort_open_ages) >= 3:
        flags.append("stuck_task_protocol")
    if admin_created and admin_closed == 0:
        flags.append("admin_closure_risk")

    return FeedbackSnapshot(
        admin_closed=admin_closed,
        admin_created=admin_created,
        jaynice_done=jaynice_done,
        jaynice_created=jaynice_created,
        avoidance_half_life_days=avoidance_half_life_days,
        overdue_resets=overdue_resets,
        flags=flags,
    )


def render_feedback_snapshot(snapshot: FeedbackSnapshot) -> list[str]:
    lines = [
        "STATS (7d):",
        f"  admin_closure_rate: {_format_ratio(snapshot.admin_closed, snapshot.admin_created)} ({snapshot.admin_closed}/{snapshot.admin_created})",
        f"  jaynice_followthrough_rate: {_format_ratio(snapshot.jaynice_done, snapshot.jaynice_created)} ({snapshot.jaynice_done}/{snapshot.jaynice_created})",
        f"  avoidance_half_life_days: {snapshot.avoidance_half_life_days}",
        f"  overdue_resets: {snapshot.overdue_resets}",
    ]
    if snapshot.flags:
        lines.append("  flags: " + ", ".join(snapshot.flags))
    else:
        lines.append("  flags: none")
    return lines


__all__ = [
    "FeedbackSnapshot",
    "build_feedback_snapshot",
    "render_feedback_snapshot",
]
