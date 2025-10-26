import shutil
from datetime import datetime
from pathlib import Path

import yaml

from .lib.sqlite import DB_PATH, LIFE_DIR

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


def backup():
    """Create timestamped backup of .life/ directory"""
    BACKUP_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / timestamp
    shutil.copytree(LIFE_DIR, backup_path, dirs_exist_ok=True)

    return backup_path


def restore(backup_name: str):
    """Restore from a backup"""
    backup_path = BACKUP_DIR / backup_name

    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {backup_name}")

    LIFE_DIR.mkdir(exist_ok=True)

    db_file = backup_path / "store.db"
    if db_file.exists():
        shutil.copy2(db_file, DB_PATH)

    config_file = backup_path / "config.yaml"
    if config_file.exists():
        shutil.copy2(config_file, CONFIG_PATH)

    ctx_file = backup_path / "context.md"
    if ctx_file.exists():
        shutil.copy2(ctx_file, CONFIG_PATH / ".context_legacy")

    profile_file = backup_path / "profile.md"
    if profile_file.exists():
        shutil.copy2(profile_file, CONFIG_PATH / ".profile_legacy")


def list_backups() -> list[str]:
    """List all available backups"""
    if not BACKUP_DIR.exists():
        return []

    return sorted([d.name for d in BACKUP_DIR.iterdir() if d.is_dir()], reverse=True)


def get_or_set_profile(profile_text=None):
    """Get current profile or set it. Returns message string."""
    if profile_text:
        set_profile(profile_text)
        return f"Profile: {profile_text}"
    prof = get_profile()
    return f"Profile: {prof if prof else '(none)'}"


def get_or_set_context(context_text=None):
    """Get current context or set it. Returns message string."""
    if context_text:
        set_context(context_text)
        return f"Context: {context_text}"
    ctx = get_context()
    return f"Context: {ctx if ctx else '(none)'}"


def get_countdowns() -> list[dict]:
    """Get list of countdowns from config"""
    config = _load_config()
    return config.get("countdowns", [])


def add_countdown(name: str, date: str, emoji: str = "📌") -> None:
    """Add a countdown to config"""
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
    """Remove a countdown from config"""
    config = _load_config()
    if "countdowns" in config:
        config["countdowns"] = [c for c in config["countdowns"] if c.get("name") != name]
        _save_config(config)
