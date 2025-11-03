from pathlib import Path

import yaml

LIFE_DIR = Path.home() / ".life"
DB_PATH = LIFE_DIR / "store.db"
CONFIG_PATH = LIFE_DIR / "config.yaml"
BACKUP_DIR = Path.home() / ".life_backups"


class Config:
    """Single-instance config manager. Load once, cache in memory."""

    _instance = None
    _data = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        """Load config from disk."""
        if not CONFIG_PATH.exists():
            self._data = {}
            return
        try:
            with open(CONFIG_PATH) as f:
                self._data = yaml.safe_load(f) or {}
        except Exception:
            self._data = {}

    def _save(self) -> None:
        """Persist config to disk."""
        LIFE_DIR.mkdir(exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(self._data, f, default_flow_style=False, allow_unicode=True)

    def get(self, key: str, default=None):
        """Get config value."""
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        """Set config value and persist."""
        self._data[key] = value
        self._save()


_config = Config()


def get_context():
    """Get current life context"""
    context = _config.get("context", "").strip()
    return context if context else "No context set"


def set_context(context):
    """Set current life context"""
    _config.set("context", context)


def get_profile():
    """Get current profile"""
    return _config.get("profile", "").strip()


def set_profile(profile):
    """Set current profile"""
    _config.set("profile", profile)


def get_default_persona() -> str | None:
    """Get default persona from config, or None if not set."""
    return _config.get("default_persona")


def set_default_persona(persona: str) -> None:
    """Set default persona in config."""
    _config.set("default_persona", persona)


def get_dates() -> list[dict]:
    """Get list of dates from config."""
    return _config.get("dates", [])


def add_date(name: str, date: str, emoji: str = "📌") -> None:
    """Add a date to config."""
    dates = _config.get("dates", [])
    dates.append({"name": name, "date": date, "emoji": emoji})
    _config.set("dates", dates)


def remove_date(name: str) -> None:
    """Remove a date from config."""
    dates = _config.get("dates", [])
    filtered = [d for d in dates if d.get("name") != name]
    _config.set("dates", filtered)
