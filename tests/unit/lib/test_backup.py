from life.lib.backup import backup


def test_backup_creates_dir(tmp_life_dir):
    result = backup()
    assert result["path"].exists()
    assert result["path"].is_dir()


def test_backup_contains_db(tmp_life_dir):
    result = backup()
    assert (result["path"] / "life.db").exists()


def test_backup_timestamp_format(tmp_life_dir):
    result = backup()
    name = result["path"].name
    assert name[:8].isdigit()
    assert name[8] == "_"
    assert name[9:15].isdigit()
    assert name[15] == "_"
    assert name[16:].isdigit()


def test_backup_in_backup_dir(tmp_life_dir):
    result = backup()
    assert str(result["path"]).startswith(str(tmp_life_dir / "backups"))


def test_backup_excludes_backups_subdir(tmp_life_dir):
    result = backup()
    assert not (result["path"] / "backups").exists()


def test_backup_integrity_ok(tmp_life_dir):
    result = backup()
    assert result["integrity_ok"] is True


def test_backup_has_row_count(tmp_life_dir):
    result = backup()
    assert isinstance(result["rows"], int)
    assert result["rows"] >= 0


def test_backup_first_has_no_delta(tmp_life_dir):
    result = backup()
    assert result["delta_total"] is None


def test_backup_second_has_delta(tmp_life_dir):
    backup()
    result = backup()
    assert result["delta_total"] is not None
