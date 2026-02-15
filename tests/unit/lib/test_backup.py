from pathlib import Path

from life.lib.backup import backup


def test_backup_creates_file(tmp_life_dir):
    backup_path = backup()
    assert backup_path.exists()
    assert backup_path.is_dir()


def test_backup_returns_path(tmp_life_dir):
    backup_path = backup()
    assert isinstance(backup_path, Path)


def test_backup_timestamp_format(tmp_life_dir):
    backup_path = backup()
    name = backup_path.name
    assert len(name) == 15
    assert name[:8].isdigit()
    assert name[8] == "_"
    assert name[9:].isdigit()


def test_backup_creates_in_backup_dir(tmp_life_dir):
    backup_path = backup()
    assert str(backup_path).startswith(str(tmp_life_dir / "backups"))


def test_backup_copies_db_file(tmp_life_dir):
    backup_path = backup()
    db_file = backup_path / "store.db"
    assert db_file.exists()


def test_backup_excludes_backups_dir(tmp_life_dir):
    backup_path = backup()
    backups_subdir = backup_path / "backups"
    assert not backups_subdir.exists()
