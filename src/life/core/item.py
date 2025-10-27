from ..lib import store


def add_item(content, focus=False, due=None, target_count=5, tags=None):
    return store.add_item(content, focus, due, target_count, tags)


def get_pending_items(asc=True):
    return store.get_pending_items(asc=asc)


def today_completed():
    return store.get_today_completed()


def weekly_momentum():
    return store.get_weekly_momentum()


def complete_item(item_id):
    store.complete_item(item_id)


def uncomplete_item(item_id):
    store.uncomplete_item(item_id)


def update_item(item_id, content=None, due=None, focus=None):
    store.update_item(item_id, content, due, focus)


def toggle_focus(item_id, current_focus):
    return store.toggle_focus(item_id, current_focus)


def delete_item(item_id):
    store.delete_item(item_id)


def get_today_completed():
    return store.get_completed_today()


def is_repeating(item_id):
    from .tag import get_tags

    tags = get_tags(item_id)
    return any(tag in ("habit", "chore") for tag in tags)


def add_task(content, focus=False, due=None, done=False, tags=None):
    item_id = add_item(content, focus=focus, due=due, tags=tags)
    if done:
        complete_item(item_id)

    focus_str = " [FOCUS]" if focus else ""
    due_str = f" due {due}" if due else ""
    tag_list = [f"#{t}" for t in tags] if tags else []
    tag_str = f" {' '.join(tag_list)}" if tag_list else ""

    if done:
        return f"✓ {content}{focus_str}{due_str}{tag_str}"
    return f"Added: {content}{focus_str}{due_str}{tag_str}"


def add_habit(content):
    add_item(content, tags=["habit"])
    return f"Added habit: {content}"


def add_chore(content):
    add_item(content, tags=["chore"])
    return f"Added chore: {content}"


def done_item(partial, undo=False):
    from ..lib.match import find_item
    from ..lib.ops import complete, uncomplete
    from .tag import get_tags

    if not partial:
        return "No item specified"

    if undo:
        uncompleted = uncomplete(partial)
        return f"✓ {uncompleted}" if uncompleted else f"No match for: {partial}"

    completed = complete(partial)
    if not completed:
        return f"No match for: {partial}"

    item = find_item(partial)
    if item:
        tags = get_tags(item[0])
        tags_str = " " + " ".join(f"#{t}" for t in tags) if tags else ""
        return f"✓ {completed}{tags_str}"
    return f"✓ {completed}"
