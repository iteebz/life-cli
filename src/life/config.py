import shutil
from datetime import datetime
from pathlib import Path

import yaml

from .lib.sqlite import DB_PATH, LIFE_DIR

CONTEXT_MD = LIFE_DIR / "context.md"
PROFILE_MD = LIFE_DIR / "profile.md"
CONFIG_PATH = LIFE_DIR / "config.yaml"
BACKUP_DIR = Path.home() / ".life_backups"


def get_context():
    """Get current life context"""
    if CONTEXT_MD.exists():
        return CONTEXT_MD.read_text().strip()
    return "No context set"


def set_context(context):
    """Set current life context"""
    LIFE_DIR.mkdir(exist_ok=True)
    CONTEXT_MD.write_text(context)


def get_profile():
    """Get current profile"""
    if PROFILE_MD.exists():
        return PROFILE_MD.read_text().strip()
    return ""


def set_profile(profile):
    """Set current profile"""
    LIFE_DIR.mkdir(exist_ok=True)
    PROFILE_MD.write_text(profile)


def get_default_persona() -> str | None:
    """Get default persona from config, or None if not set."""
    if not CONFIG_PATH.exists():
        return None
    try:
        with open(CONFIG_PATH) as f:
            config = yaml.safe_load(f) or {}
        return config.get("default_persona")
    except Exception:
        return None


def set_default_persona(persona: str) -> None:
    """Set default persona in config."""
    LIFE_DIR.mkdir(exist_ok=True)
    config = {}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                config = yaml.safe_load(f) or {}
        except Exception:
            pass
    config["default_persona"] = persona
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f)


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

    ctx_file = backup_path / "context.md"
    if ctx_file.exists():
        shutil.copy2(ctx_file, CONTEXT_MD)

    profile_file = backup_path / "profile.md"
    if profile_file.exists():
        shutil.copy2(profile_file, PROFILE_MD)


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
    else:
        prof = get_profile()
        return f"Profile: {prof if prof else '(none)'}"


def get_or_set_context(context_text=None):
    """Get current context or set it. Returns message string."""
    if context_text:
        set_context(context_text)
        return f"Context: {context_text}"
    else:
        ctx = get_context()
        return f"Context: {ctx if ctx else '(none)'}"
