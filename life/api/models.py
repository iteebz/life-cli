import dataclasses
from datetime import date, datetime


@dataclasses.dataclass(frozen=True)
class Item:
    id: str
    content: str
    focus: bool
    due: date | None
    created: datetime
    completed: datetime | None
    is_repeat: bool = False


@dataclasses.dataclass(frozen=True)
class Check:
    item_id: str
    check_date: date


@dataclasses.dataclass(frozen=True)
class Tag:
    item_id: str
    tag: str


@dataclasses.dataclass(frozen=True)
class Weekly:
    tasks_completed: int = 0
    tasks_total: int = 0
    habits_completed: int = 0
    habits_total: int = 0
    chores_completed: int = 0
    chores_total: int = 0
