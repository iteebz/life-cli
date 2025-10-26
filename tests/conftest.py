import pytest


@pytest.fixture
def tmp_life_dir(monkeypatch, tmp_path):
    db_path = tmp_path / "store.db"
    cfg_path = tmp_path / "config.yaml"

    monkeypatch.setattr("life.lib.sqlite.LIFE_DIR", tmp_path)
    monkeypatch.setattr("life.lib.sqlite.DB_PATH", db_path)
    monkeypatch.setattr("life.lib.store.DB_PATH", db_path)
    monkeypatch.setattr("life.config.LIFE_DIR", tmp_path)
    monkeypatch.setattr("life.config.CONFIG_PATH", cfg_path)
    monkeypatch.setattr("life.config.BACKUP_DIR", tmp_path / "backups")
    yield tmp_path
