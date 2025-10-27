"""Ephemeral Claude invocation for persona-driven insights."""

import os
import subprocess
import sys
from pathlib import Path

from ..app.render import Spinner, render_dashboard
from ..config import get_context, get_profile
from ..core.item import get_pending_items, get_today_completed, today_completed, weekly_momentum
from ..lib.ansi import ANSI, PERSONA_COLORS, md_to_ansi


def build_context() -> str:
    """Build context for ephemeral claude invocation."""
    items = get_pending_items()
    today_count = today_completed()
    momentum = weekly_momentum()
    life_context = get_context()
    today_items = get_today_completed()
    return render_dashboard(items, today_count, momentum, life_context, today_items)


def invoke(message: str, persona: str = "roast") -> None:
    """Spawn ephemeral Claude persona and invoke with message.

    Temporarily swaps ~/.claude/CLAUDE.md with persona constitution,
    executes one Claude invocation, then restores original.
    """
    from ..personas import get_persona as get_persona_instructions

    persona_instructions = get_persona_instructions(persona)
    profile = get_profile()

    profile_section = f"PROFILE:\n{profile}\n\n" if profile else ""

    task_prompt = f"""{persona_instructions}

{profile_section}---
USER MESSAGE: {message}

RESPONSE PROTOCOL:
- Be concise and direct
- Use `life` CLI output to assess current state
- Provide actionable analysis or next steps
- Format markdown for bold/emphasis where helpful"""

    env = os.environ.copy()
    env["LIFE_PERSONA"] = persona

    claude_path = Path.home() / ".claude" / "CLAUDE.md"
    original_content = claude_path.read_text() if claude_path.exists() else ""

    try:
        claude_path.parent.mkdir(parents=True, exist_ok=True)
        claude_path.write_text(persona_instructions)

        spinner = Spinner(persona)
        spinner.start()

        result = subprocess.run(
            ["claude", "--model", "claude-haiku-4-5", "-p", task_prompt, "--allowedTools", "Bash"],
            env=env,
            capture_output=True,
            text=True,
        )

        spinner.stop()

        formatted = md_to_ansi(result.stdout)
        color = PERSONA_COLORS.get(persona, ANSI.WHITE)
        header = f"\n{ANSI.BOLD}{color}[{persona}]:{ANSI.RESET}\n\n"
        sys.stdout.write(header + formatted + "\n")
    finally:
        if original_content:
            claude_path.write_text(original_content)
        elif claude_path.exists():
            claude_path.unlink()
