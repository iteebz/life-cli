import dataclasses
from datetime import date, datetime


@dataclasses.dataclass(frozen=True)
class Task:
    id: str
    content: str
    focus: bool
    due_date: date | None
    created: datetime
    completed_at: datetime | None
    parent_id: str | None = None
    scheduled_time: str | None = None
    blocked_by: str | None = None
    tags: list[str] = dataclasses.field(default_factory=list, hash=False)


@dataclasses.dataclass(frozen=True)
class Habit:
    id: str
    content: str
    created: datetime
    checks: list[date] = dataclasses.field(default_factory=list, hash=False)
    tags: list[str] = dataclasses.field(default_factory=list, hash=False)


@dataclasses.dataclass(frozen=True)
class Tag:
    tag: str
    task_id: str | None = None
    habit_id: str | None = None


@dataclasses.dataclass(frozen=True)
class Weekly:
    tasks_completed: int = 0
    tasks_total: int = 0
    habits_completed: int = 0
    habits_total: int = 0
