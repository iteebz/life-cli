import sys

from fncli import cli

from .habits import check_habit_cmd, rename_habit
from .lib.ansi import ANSI
from .lib.errors import echo, exit_error
from .lib.resolve import resolve_item, resolve_item_any
from .models import Task
from .tasks import check_task_cmd, delete_task, rename_task


def _animate_uncheck(label: str) -> None:
    sys.stdout.write(f"  \u25a1 {ANSI.GREY}{label}{ANSI.RESET}\n")
    sys.stdout.flush()


@cli("life")
def check(ref: list[str]) -> None:
    """Mark task/habit as done"""
    item_ref = " ".join(ref) if ref else ""
    if not item_ref:
        exit_error("Usage: life check <item>")
    task, habit = resolve_item_any(item_ref)
    if habit:
        check_habit_cmd(habit)
    elif task:
        check_task_cmd(task)


@cli("life")
def done(ref: list[str]) -> None:
    """Alias for check"""
    item_ref = " ".join(ref) if ref else ""
    if not item_ref:
        exit_error("Usage: life done <item>")
    task, habit = resolve_item_any(item_ref)
    if habit:
        check_habit_cmd(habit)
    elif task:
        check_task_cmd(task)


@cli("life")
def uncheck(ref: list[str]) -> None:
    """Unmark task/habit as done"""
    from .habits import get_checks, toggle_check
    from .lib.clock import today
    from .tasks import uncheck_task

    item_ref = " ".join(ref) if ref else ""
    if not item_ref:
        exit_error("Usage: life uncheck <item>")
    task, habit = resolve_item_any(item_ref)
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


@cli("life", name="rm")
def rm(ref: list[str]) -> None:
    """Delete item or completed task (fuzzy match)"""
    from .habits import delete_habit

    item_ref = " ".join(ref) if ref else ""
    if not item_ref:
        exit_error("Usage: life rm <item>")
    task, habit = resolve_item_any(item_ref)
    if task:
        delete_task(task.id)
        echo(f"{ANSI.DIM}{task.content}{ANSI.RESET}")
    elif habit:
        delete_habit(habit.id)
        echo(f"{ANSI.DIM}{habit.content}{ANSI.RESET}")


@cli("life")
def add(
    content: list[str],
    habit: bool = False,
    focus: bool = False,
    due: str | None = None,
    tag: list[str] | None = None,
    under: str | None = None,
    desc: str | None = None,
    done: bool = False,
    steward: bool = False,
    source: str | None = None,
) -> None:
    """Add task or habit (--habit)"""
    from .habits import habit as habit_cmd
    from .tasks import task as task_cmd

    if habit:
        habit_cmd(content=content, tag=tag, under=under)
        return
    task_cmd(
        content=content,
        focus=focus,
        due=due,
        tag=tag,
        under=under,
        desc=desc,
        done=done,
        steward=steward,
        source=source,
    )


@cli("life")
def rename(ref: list[str], to: str) -> None:
    """Rename an item"""
    if not to:
        exit_error("Error: 'to' content cannot be empty.")
    item_ref = " ".join(ref) if ref else ""
    task, habit = resolve_item(item_ref)
    if not task and not habit:
        exit_error("Error: Item not found.")
    if isinstance(task, Task):
        rename_task(task, to)
    elif habit:
        rename_habit(habit, to)
