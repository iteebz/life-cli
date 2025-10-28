from .items import toggle_done


def done_item(partial, undo=False):
    if not partial:
        return "No item specified"

    result = toggle_done(partial, undo=undo)

    if result:
        status, content = result
        # The checkmark is added by the CLI layer, not ops layer
        return content
    return f"No match for: {partial}"
