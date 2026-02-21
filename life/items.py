import sys
import time

from .habits import cmd_check_habit, cmd_rename_habit, delete_habit
from .lib.ansi import ANSI
from .lib.errors import echo, exit_error
from .lib.resolve import resolve_item, resolve_item_any
from .models import Task
from .tasks import cmd_check_task, cmd_rename_task, delete_task

__all__ = [
    "cmd_check",
    "cmd_rename",
    "cmd_rm",
    "cmd_uncheck",
]


def _animate_uncheck(label: str) -> None:
    sys.stdout.write(f"  {ANSI.GREY}\u2713{ANSI.RESET} {label}")
    sys.stdout.flush()
    time.sleep(0.18)
    sys.stdout.write(f"\r  \u25a1 {label}\n")
    sys.stdout.flush()


def cmd_check(args: list[str]) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life check <item>")
    task, habit = resolve_item_any(ref)
    if habit:
        cmd_check_habit(habit)
    elif task:
        cmd_check_task(task)


def cmd_uncheck(args: list[str]) -> None:
    from .habits import get_checks, toggle_check
    from .lib.clock import today
    from .tasks import uncheck_task

    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life uncheck <item>")
    task, habit = resolve_item_any(ref)
    if habit:
        today_date = today()
        checks = get_checks(habit.id)
        checked_today = any(c.date() == today_date for c in checks)
        if not checked_today:
            exit_error(f"'{habit.content}' is not checked today")
        updated = toggle_check(habit.id)
        if updated:
            checked_today = any(c.date() == today() for c in updated.checks)
            if not checked_today:
                _animate_uncheck(habit.content.lower())
    elif task:
        if not task.completed_at:
            exit_error(f"'{task.content}' is not done")
        uncheck_task(task.id)
        _animate_uncheck(task.content.lower())


def cmd_rm(args: list[str]) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life rm <item>")
    task, habit = resolve_item_any(ref)
    if task:
        delete_task(task.id)
        echo(f"{ANSI.DIM}{task.content}{ANSI.RESET}")
    elif habit:
        delete_habit(habit.id)
        echo(f"{ANSI.DIM}{habit.content}{ANSI.RESET}")


def cmd_rename(from_args: list[str], to_content: str) -> None:
    if not to_content:
        exit_error("Error: 'to' content cannot be empty.")
    ref = " ".join(from_args) if from_args else ""
    task, habit = resolve_item(ref)
    if not task and not habit:
        exit_error("Error: Item not found.")
    if isinstance(task, Task):
        cmd_rename_task(task, to_content)
    elif habit:
        cmd_rename_habit(habit, to_content)
