import pytest


@pytest.fixture
def tmp_life_dir(monkeypatch, tmp_path):
    db_path = tmp_path / "store.db"
    ctx_path = tmp_path / "context.md"
    prof_path = tmp_path / "profile.md"
    cfg_path = tmp_path / "config.yaml"

    monkeypatch.setattr("life.lib.sqlite.LIFE_DIR", tmp_path)
    monkeypatch.setattr("life.lib.sqlite.DB_PATH", db_path)
    monkeypatch.setattr("life.core.item.DB_PATH", db_path)
    monkeypatch.setattr("life.core.tag.DB_PATH", db_path)
    monkeypatch.setattr("life.config.LIFE_DIR", tmp_path)
    monkeypatch.setattr("life.config.CONTEXT_MD", ctx_path)
    monkeypatch.setattr("life.config.PROFILE_MD", prof_path)
    monkeypatch.setattr("life.config.CONFIG_PATH", cfg_path)
    monkeypatch.setattr("life.config.BACKUP_DIR", tmp_path / "backups")
    monkeypatch.setattr("life.core.repeat.DB_PATH", db_path)
    yield tmp_path
