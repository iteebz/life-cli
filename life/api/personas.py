"""Persona management and definitions."""

from ..api import weekly_momentum
from ..config import get_context, get_default_persona, get_profile, set_default_persona
from ..lib.render import render_dashboard
from .dashboard import get_pending_items, get_today_breakdown, get_today_completed


def _get_personas():
    """Lazy load personas to avoid circular imports."""
    from ..personas.kim import kim
    from ..personas.pepper import pepper
    from ..personas.roast import roast

    return {
        "roast": roast,
        "pepper": pepper,
        "kim": kim,
    }


def get_persona(name: str = "roast") -> str:
    """Get persona instructions by name. Defaults to roast."""
    personas = _get_personas()
    if name not in personas:
        raise ValueError(f"Unknown persona: {name}. Available: {list(personas.keys())}")
    return personas[name]()


def get_default_persona_name() -> str | None:
    """Get default persona name from config, or None if not set."""
    return get_default_persona()


def set_default_persona_name(persona: str) -> None:
    """Set default persona name in config."""
    set_default_persona(persona)


def _list_personas() -> str:
    """Display all available personas with descriptions and default marker."""
    descriptions = {
        "roast": "The mirror. Call out patterns, push back on bullshit.",
        "pepper": "Pepper Potts energy. Optimistic enabler. Unlock potential.",
        "kim": "Lieutenant Kim Kitsuragi. Methodical clarity. Work the case.",
    }
    lines = ["Available personas:"]
    curr_default = get_default_persona_name()
    for p in ("roast", "pepper", "kim"):
        marker = "# " if p == curr_default else "  "
        lines.append(f"{marker}{p:8} - {descriptions[p]}")
    return "\n".join(lines)


def _resolve_persona_alias(name: str) -> str:
    """Resolve persona name aliases and validate against known personas."""
    aliases = {"kitsuragi": "kim"}
    resolved = aliases.get(name, name)
    if resolved not in ("roast", "pepper", "kim"):
        raise ValueError(f"Unknown persona: {resolved}")
    return resolved


def _build_persona_prompt(persona_name: str) -> str:
    """Build full persona prompt with current life context."""
    persona_instructions = get_persona(persona_name)
    profile = get_profile()
    context = get_context()

    items = get_pending_items()
    today_items = get_today_completed()
    today_breakdown = get_today_breakdown()
    momentum = weekly_momentum()
    life_output = render_dashboard(
        items, today_breakdown, momentum, context, today_items
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


def manage_personas(name=None, set_default=False, show_prompt=False):
    """Show personas, view/set one, or show full prompt. Returns message string."""
    if not name:
        return _list_personas()

    resolved_name = _resolve_persona_alias(name)

    if set_default:
        set_default_persona_name(resolved_name)
        return f"Default persona set to: {resolved_name}"
    
    if show_prompt:
        return _build_persona_prompt(resolved_name)
    
    return get_persona(resolved_name)


__all__ = [
    "get_persona",
    "manage_personas",
    "get_default_persona_name",
]
