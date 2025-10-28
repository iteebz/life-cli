from pathlib import Path

import yaml

LIFE_DIR = Path.home() / ".life"
DB_PATH = LIFE_DIR / "store.db"
CONFIG_PATH = LIFE_DIR / "config.yaml"
BACKUP_DIR = Path.home() / ".life_backups"


def _load_config() -> dict:
    """Load config.yaml, return empty dict if not found"""
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _save_config(config: dict) -> None:
    """Save config to YAML"""
    LIFE_DIR.mkdir(exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def get_context():
    """Get current life context"""
    config = _load_config()
    context = config.get("context", "").strip()
    return context if context else "No context set"


def set_context(context):
    """Set current life context"""
    config = _load_config()
    config["context"] = context
    _save_config(config)


def get_profile():
    """Get current profile"""
    config = _load_config()
    return config.get("profile", "").strip()


def set_profile(profile):
    """Set current profile"""
    config = _load_config()
    config["profile"] = profile
    _save_config(config)


def get_default_persona() -> str | None:
    """Get default persona from config, or None if not set."""
    config = _load_config()
    return config.get("default_persona")


def set_default_persona(persona: str) -> None:
    """Set default persona in config."""
    config = _load_config()
    config["default_persona"] = persona
    _save_config(config)


def get_countdowns() -> list[dict]:
    """Get list of countdowns from config."""
    config = _load_config()
    return config.get("countdowns", [])


def add_countdown(name: str, date: str, emoji: str = "📌") -> None:
    """Add a countdown to config."""
    config = _load_config()
    if "countdowns" not in config:
        config["countdowns"] = []
    config["countdowns"].append(
        {
            "name": name,
            "date": date,
            "emoji": emoji,
        }
    )
    _save_config(config)


def remove_countdown(name: str) -> None:
    """Remove a countdown from config."""
    config = _load_config()
    if "countdowns" in config:
        config["countdowns"] = [c for c in config["countdowns"] if c.get("name") != name]
        _save_config(config)
