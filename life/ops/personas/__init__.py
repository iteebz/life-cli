"""Persona management and definitions."""

import sys

from ...api import (
    get_pending_items,
    get_today_breakdown,
    get_today_completed,
    weekly_momentum,
)
from ...config import get_context, get_default_persona, get_profile, set_default_persona
from ...lib.claude import invoke as invoke_claude
from ...lib.render import render_dashboard
from .kim import kim
from .pepper import pepper
from .roast import roast

PERSONAS = {
    "roast": roast,
    "pepper": pepper,
    "kim": kim,
}


def get_persona(name: str = "roast") -> str:
    """Get persona instructions by name. Defaults to roast."""
    if name not in PERSONAS:
        raise ValueError(f"Unknown persona: {name}. Available: {list(PERSONAS.keys())}")
    return PERSONAS[name]()


def get_default_persona_name() -> str | None:
    """Get default persona name from config, or None if not set."""
    return get_default_persona()


def set_default_persona_name(persona: str) -> None:
    """Set default persona name in config."""
    set_default_persona(persona)


def manage_personas(name=None, set_default=False, show_prompt=False):
    """Show personas, view/set one, or show full prompt. Returns message string."""
    descriptions = {
        "roast": "The mirror. Call out patterns, push back on bullshit.",
        "pepper": "Pepper Potts energy. Optimistic enabler. Unlock potential.",
        "kim": "Lieutenant Kim Kitsuragi. Methodical clarity. Work the case.",
    }

    if not name:
        lines = ["Available personas:"]
        curr_default = get_default_persona_name()
        for p in ("roast", "pepper", "kim"):
            marker = "# " if p == curr_default else "  "
            lines.append(f"{marker}{p:8} - {descriptions[p]}")
        return "\n".join(lines)

    aliases = {"kitsuragi": "kim"}
    resolved_name = aliases.get(name, name)
    if resolved_name not in ("roast", "pepper", "kim"):
        raise ValueError(f"Unknown persona: {resolved_name}")

    if set_default:
        set_default_persona_name(resolved_name)
        return f"Default persona set to: {resolved_name}"
    if show_prompt:
        try:
            persona_instructions = get_persona(resolved_name)
            profile = get_profile()
            context = get_context()

            items = get_pending_items()
            life_context_data = get_context()
            today_items = get_today_completed()
            today_breakdown = get_today_breakdown()
            momentum = weekly_momentum()
            life_output = render_dashboard(
                items, today_breakdown, momentum, life_context_data, today_items
            ).lstrip()

            profile_section = f"PROFILE:\n{profile if profile else '(no profile set)'}"
            context_section = f"CONTEXT:\n{context if context and context != 'No context set' else '(no context set)'}"

            sections = [
                persona_instructions,
                ";",
                profile_section,
                context_section,
                ";",
                f"CURRENT LIFE STATE:\n{life_output}",
                ";",
                "USER MESSAGE: [your message here]",
            ]

            return "\n\n".join(sections)
        except ValueError as e:
            raise ValueError(str(e)) from None
    else:
        try:
            return get_persona(resolved_name)
        except ValueError as e:
            raise ValueError(str(e)) from None


def _get_known_commands() -> set[str]:
    """Dynamically build set of known commands from cli/ directory and explicit aliases."""
    return {
        "help",
        "--help",
        "-h",
        "chat",
        "task",
        "add",
        "habit",
        "chore",
        "done",
        "rm",
        "focus",
        "due",
        "rename",
        "tag",
        "profile",
        "context",
        "countdown",
        "backup",
        "personas",
    }


KNOWN_COMMANDS = _get_known_commands()


def _is_message(raw_args: list[str]) -> bool:
    """Check if args represent a chat message (not a command)."""
    if not raw_args:
        return False
    first_arg = raw_args[0].lower()
    return first_arg not in KNOWN_COMMANDS and not first_arg.startswith("-")


def maybe_spawn_persona() -> bool:
    """Check if we should spawn persona. Returns True if spawned."""
    raw_args = sys.argv[1:]

    if not raw_args or raw_args[0] in ("--help", "-h", "--show-completion", "--install-completion"):
        return False

    valid_personas = {"roast", "pepper", "kim"}

    if raw_args[0] in valid_personas:
        persona = raw_args[0]
        raw_args = raw_args[1:]
        if _is_message(raw_args):
            message = " ".join(raw_args)
            invoke_claude(message, persona)
            return True
    elif _is_message(raw_args):
        default = get_default_persona_name() or "roast"
        message = " ".join(raw_args)
        invoke_claude(message, default)
        return True

    return False


__all__ = [
    "get_persona",
    "manage_personas",
    "maybe_spawn_persona",
]
