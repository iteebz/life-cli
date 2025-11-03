"""Ephemeral Claude invocation for persona-driven insights."""

import contextlib
import os
import subprocess
import sys
from pathlib import Path

from ..config import get_profile
from ..lib.ansi import ANSI, PERSONA_COLORS, md_to_ansi
from ..lib.spinner import Spinner


def _build_prompt(message: str, persona: str) -> str:
    """Construct task prompt with persona instructions and user message."""
    from ..api.personas import get_persona

    persona_instructions = get_persona(persona)
    profile = get_profile()
    profile_section = f"PROFILE:\n{profile}\n\n" if profile else ""

    return f"""{persona_instructions}

{profile_section}---
USER MESSAGE: {message}

RESPONSE PROTOCOL:
- Be concise and direct
- Use `life` CLI output to assess current state
- Provide actionable analysis or next steps
- Format markdown for bold/emphasis where helpful"""


@contextlib.contextmanager
def _ephemeral_claude_md(persona: str):
    """Context manager for temporary CLAUDE.md swapping.

    Creates persona constitution file, restores or deletes on exit.
    """
    from ..api.personas import get_persona

    claude_path = Path.home() / ".claude" / "CLAUDE.md"
    original_content = claude_path.read_text() if claude_path.exists() else ""

    try:
        claude_path.parent.mkdir(parents=True, exist_ok=True)
        claude_path.write_text(get_persona(persona))
        yield claude_path
    finally:
        if original_content:
            claude_path.write_text(original_content)
        elif claude_path.exists():
            claude_path.unlink()


def _run_claude_subprocess(prompt: str, persona: str) -> str:
    """Execute Claude subprocess with prompt. Returns stdout."""
    env = os.environ.copy()
    env["LIFE_PERSONA"] = persona

    spinner = Spinner(persona)
    spinner.start()

    try:
        result = subprocess.run(
            ["claude", "--model", "claude-haiku-4-5", "-p", prompt, "--allowedTools", "Bash"],
            env=env,
            capture_output=True,
            text=True,
        )
        return result.stdout
    finally:
        spinner.stop()


def _format_output(message: str, persona: str) -> str:
    """Format Claude response with persona header."""
    formatted = md_to_ansi(message)
    color = PERSONA_COLORS.get(persona, ANSI.WHITE)
    header = f"\n{ANSI.BOLD}{color}[{persona}]:{ANSI.RESET}\n\n"
    return header + formatted + "\n"


def invoke(message: str, persona: str = "roast") -> None:
    """Spawn ephemeral Claude persona and invoke with message.

    Orchestrates: prompt construction → file setup → subprocess → output.
    """
    prompt = _build_prompt(message, persona)

    with _ephemeral_claude_md(persona):
        output = _run_claude_subprocess(prompt, persona)

    sys.stdout.write(_format_output(output, persona))
