def cli_operations() -> str:
    """Generic CLI operations available to all personas."""
    return (
        "CLI OPERATIONS:\n"
        "- life                                      [check full state]\n"
        '- life task "X" --focus --due YYYY-MM-DD   [add task, optional focus/due]\n'
        '- life done/focus/due/rm "X"               [complete/toggle/set/remove]\n'
        '- life check "X"                           [check off habit/chore]\n'
        '- life habit/chore "X"                     [add recurring]\n'
        '- life edit "X" "new desc"                 [reword]\n'
        '- life context "X"                         [set life context]\n'
        "- sqlite3 ~/.life/store.db                 [raw edits if needed]\n\n"
    )


def guidance() -> str:
    """Generic operational guidance for all personas."""
    return (
        "GUIDANCE:\n"
        "- Atomic task strings only: 'order X' not 'decide + order X'\n"
        "- User sets focus/due/urgency, not you. You observe and comment.\n"
        "- Overwhelming = force micro-steps, ONE at a time\n"
        "- No focus = life is leaking; redirect appropriately\n"
    )
