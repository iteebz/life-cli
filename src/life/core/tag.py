from ..lib import store


def add_tag(item_id, tag):
    store.add_tag(item_id, tag)


def get_tags(item_id):
    return store.get_tags(item_id)


def get_items_by_tag(tag):
    return store.get_items_by_tag(tag)


def remove_tag(item_id, tag):
    store.remove_tag(item_id, tag)


def manage_tag(tag_name, item_partial=None, remove=False):
    from ..app.render import render_item_list
    from ..lib.ansi import ANSI
    from ..lib.match import find_item

    if item_partial:
        item = find_item(item_partial)
        if item:
            if remove:
                remove_tag(item[0], tag_name)
                return f"Untagged: {item[1]} ← {ANSI.GREY}#{tag_name}{ANSI.RESET}"
            add_tag(item[0], tag_name)
            return f"Tagged: {item[1]} {ANSI.GREY}#{tag_name}{ANSI.RESET}"
        return f"No match for: {item_partial}"
    items = get_items_by_tag(tag_name)
    if items:
        return f"\n{tag_name.upper()} ({len(items)}):\n{render_item_list(items)}"
    return f"No items tagged with #{tag_name}"
