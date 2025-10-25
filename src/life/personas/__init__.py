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
