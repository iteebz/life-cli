"""Ephemeral Claude invocation for persona-driven insights."""

import os
import subprocess
import sys

from .config import get_context, get_profile
from .display import Spinner
from .lib.ansi import ANSI, PERSONA_COLORS, md_to_ansi
from .tasks import get_pending_items, get_today_completed, today_completed, weekly_momentum


def build_context() -> str:
	"""Build context for ephemeral claude invocation."""
	items = get_pending_items()
	today_count = today_completed()
	momentum = weekly_momentum()
	life_context = get_context()
	today_items = get_today_completed()
	from .display import render_dashboard
	return render_dashboard(items, today_count, momentum, life_context, today_items)


def invoke(message: str, persona: str = "roast") -> None:
	"""Spawn ephemeral Claude persona and invoke with message."""
	from .personas import get_persona

	persona_instructions = get_persona(persona)
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
