import typer

from ..api import add_item
from ..ops import _parse_due_date
from ..ops.items import complete

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def task(
    content: list[str] = typer.Argument(..., help="Task content"),  # noqa: B008
    focus: bool = typer.Option(False, "-f", "--focus", help="Mark as focus item"),  # noqa: B008
    due: str = typer.Option(
        None, "-d", "--due", help="Due date (today, tomorrow, day name, or YYYY-MM-DD)"
    ),  # noqa: B008
    done: bool = typer.Option(False, "-x", "--done", help="Immediately mark item as done"),  # noqa: B008
    tag: list[str] = typer.Option(None, "-t", "--tag", help="Add tags to item"),  # noqa: B008
):
    """Add task (supports focus, due date, tags, immediate completion)"""
    content_str = " ".join(content)
    due_date = _parse_due_date(due) if due else None
    if due and not due_date:
        typer.echo(f"Invalid due date: {due}")
        raise typer.Exit(1)

    item_id = add_item(content_str, focus=focus, due=due_date, tags=tag)
    if done:
        complete(str(item_id))

    focus_str = " [FOCUS]" if focus else ""
    due_str = f" due {due_date}" if due_date else ""
    tag_list = [f"#{t}" for t in tag] if tag else []
    tag_str = f" {' '.join(tag_list)}" if tag_list else ""

    if done:
        typer.echo(f"✓ {content_str}{focus_str}{due_str}{tag_str}")
    else:
        typer.echo(f"Added: {content_str}{focus_str}{due_str}{tag_str}")
