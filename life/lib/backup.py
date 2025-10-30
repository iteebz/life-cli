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
