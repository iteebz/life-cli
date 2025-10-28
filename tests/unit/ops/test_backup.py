from life.api import list_backups, restore


def test_list_backups_returns_list(tmp_life_dir):
    result = list_backups()

    assert isinstance(result, list)


def test_restore_raises_on_missing_backup(tmp_life_dir):
    try:
        restore("nonexistent_backup_xyz")
        raise AssertionError("Should raise FileNotFoundError")
    except FileNotFoundError:
        pass
