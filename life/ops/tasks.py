from ..api import get_tags
from ..lib.match import find_item
from .items import complete, uncomplete


def done_item(partial, undo=False):
    if not partial:
        return "No item specified"

    if undo:
        uncompleted = uncomplete(partial)
        return f"✓ {uncompleted}" if uncompleted else f"No match for: {partial}"

    completed = complete(partial)
    if not completed:
        return f"No match for: {partial}"

    found_item = find_item(partial)
    if found_item:
        tags = get_tags(found_item[0])
        tags_str = " " + " ".join(f"#{t}" for t in tags) if tags else ""
        return f"✓ {completed}{tags_str}"
    return f"✓ {completed}"
