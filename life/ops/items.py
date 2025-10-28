from ..api import (
    add_tag,
    delete_item,
    get_items_by_tag,
    remove_tag,
    update_item,
)
from ..lib.ansi import ANSI
from ..lib.dates import _parse_due_date
from ..lib.render import render_item_list
from ..ops.fuzzy import _find_by_partial, find_item
from .dashboard import get_pending_items, get_today_completed


def update(partial: str, **kwargs) -> str | None:
    """Update item (focus/due only on tasks, not repeating items)."""
    item = find_item(partial)
    if item:
        if any(k in kwargs for k in ("focus", "due_date")) and item.is_repeat:
            return None
        update_item(item.id, **kwargs)
        return kwargs.get("content", item.content)
    return None


def remove(partial: str) -> str | None:
    """Remove item (LIFO - most recent match)."""
    pending = get_pending_items(asc=False)
    item = _find_by_partial(partial, pending)
    if item:
        delete_item(item.id)
        return item.content

    completed_today = get_today_completed()
    item = _find_by_partial(partial, completed_today)
    if item:
        delete_item(item.id)
        return item.content

    return None


def set_due(args, remove=False) -> str:
    """Set or remove due date. Returns message string."""
    if not args:
        return "Due date and item required"

    date_str = None
    item_args = args

    if not remove and len(args) > 0:
        parsed = _parse_due_date(args[0])
        if parsed:
            date_str = parsed
            item_args = args[1:]

    if not item_args:
        return "Item name required"

    partial = " ".join(item_args)
    item = find_item(partial)
    if not item:
        return f"No match for: {partial}"

    if item.is_repeat:
        return f"Cannot set due date on repeating items: {item.content}"

    if remove:
        update_item(item.id, due_date=None)
        return f"Due date removed: {item.content}"

    if not date_str:
        return "Due date required (today, tomorrow, day name, or YYYY-MM-DD) or use -r/--remove to clear"

    update_item(item.id, due_date=date_str)
    return f"Due: {item.content} on {date_str}"


def edit_item(new_content, partial) -> str:
    """Edit item content. Returns message string."""
    result = update(partial, content=new_content)
    if result:
        return f"Updated: {result} → {new_content}"
    return f"No match for: {partial}"


def manage_tag(tag_name, item_partial=None, remove=False, include_completed=False):
    """Add, remove, or view items by tag (fuzzy match)"""
    if item_partial:
        item = None
        if include_completed:
            all_items = get_pending_items() + get_today_completed()
            item = _find_by_partial(item_partial, all_items)
        else:
            item = find_item(item_partial)

        if item:
            if remove:
                remove_tag(item.id, tag_name)
                return f"Untagged: {item.content} ← {ANSI.GREY}#{tag_name}{ANSI.RESET}"
            add_tag(item.id, tag_name)
            return f"Tagged: {item.content} {ANSI.GREY}#{tag_name} {ANSI.RESET}"
        return f"No match for: {item_partial}"
    items = get_items_by_tag(tag_name)
    if items:
        return f"\n{tag_name.upper()} ({len(items)}):\n{render_item_list(items)}"
    return f"No items tagged with #{tag_name}"
