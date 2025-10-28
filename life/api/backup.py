import shutil
from datetime import datetime

from .. import config


def backup():
    """Create timestamped backup of .life/ directory"""
    config.BACKUP_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config.BACKUP_DIR / timestamp
    shutil.copytree(
        config.LIFE_DIR, backup_path, dirs_exist_ok=True, ignore=shutil.ignore_patterns("backups")
    )

    return backup_path


def restore(backup_name: str):
    """Restore from a backup"""
    backup_path = config.BACKUP_DIR / backup_name

    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {backup_name}")

    config.LIFE_DIR.mkdir(exist_ok=True)

    db_file = backup_path / "store.db"
    if db_file.exists():
        shutil.copy2(db_file, config.DB_PATH)

    config_file = backup_path / "config.yaml"
    if config_file.exists():
        shutil.copy2(config_file, config.CONFIG_PATH)

    ctx_file = backup_path / "context.md"
    if ctx_file.exists():
        shutil.copy2(ctx_file, config.CONFIG_PATH / ".context_legacy")

    profile_file = backup_path / "profile.md"
    if profile_file.exists():
        shutil.copy2(profile_file, config.CONFIG_PATH / ".profile_legacy")


def list_backups() -> list[str]:
    """List all available backups"""
    if not config.BACKUP_DIR.exists():
        return []

    return sorted([d.name for d in config.BACKUP_DIR.iterdir() if d.is_dir()], reverse=True)
