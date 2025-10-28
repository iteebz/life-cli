import pytest

from life import db


@pytest.fixture
def tmp_life_dir(monkeypatch, tmp_path):
    db_path = tmp_path / "store.db"
    cfg_path = tmp_path / "config.yaml"

    monkeypatch.setattr("life.config.LIFE_DIR", tmp_path)
    monkeypatch.setattr("life.config.DB_PATH", db_path)
    monkeypatch.setattr("life.config.CONFIG_PATH", cfg_path)
    monkeypatch.setattr("life.config.BACKUP_DIR", tmp_path / "backups")

    db.init(db_path=db_path)
    yield tmp_path
