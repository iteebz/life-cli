from datetime import date, datetime, time

import pytest

import life.lib.clock as clock
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


@pytest.fixture
def fixed_today(monkeypatch):
    fixed_date = date(2025, 10, 30)
    monkeypatch.setattr(clock, "today", lambda: fixed_date)
    monkeypatch.setattr(clock, "now", lambda: datetime.combine(fixed_date, time.min))
    return fixed_date
