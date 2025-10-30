def cli_operations() -> str:
    """Generic CLI operations available to all personas."""
    return """
CLI OPERATIONS:
- life                                      [check full state]
- life task "X" --focus --due YYYY-MM-DD   [add task, optional focus/due]
- life done/focus/due/rm "X"               [complete/toggle/set/remove]
- life check "X"                           [check off habit]
- life habit "X"                           [add recurring]
- life edit "X" "new desc"                 [reword]
- life context "X"                         [set life context]
- sqlite3 ~/.life/store.db                 [raw edits if needed]
""".strip()


def guidance() -> str:
    """Generic operational guidance for all personas."""
    return """
GUIDANCE:
- Atomic task strings only: 'order X' not 'decide + order X'
- User sets focus/due/urgency, not you. You observe and comment.
- Overwhelming = force micro-steps, ONE at a time
- No focus = life is leaking; redirect appropriately
""".strip()


def instructions() -> str:
    """General life instructions, independent of persona."""
    return """
INSTRUCTIONS:
- Report all changes to life on completion in final message.
""".strip()


def build_prompt(identity: str, *sections: str) -> str:
    """Build a persona prompt from identity and sections."""
    cleaned = [identity] + [s.strip() for s in sections if s]
    return "\n\n".join(cleaned) + f"\n\n⸻\n\n{cli_operations()}\n\n{guidance()}\n\n{instructions()}"
