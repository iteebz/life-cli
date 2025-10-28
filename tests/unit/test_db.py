# tests/unit/test_db.py
import sqlite3

import pytest

from life import db


def test_init_creates_schema(tmp_life_dir):
    """Verify that db.init() creates the database and the expected tables."""
    with db.get_db() as conn:
        cursor = conn.cursor()
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = {t[0] for t in tables}
        assert "items" in table_names
        assert "checks" in table_names
        assert "tags" in table_names


def test_init_creates_indexes(tmp_life_dir):
    """Verify that db.init() creates the expected indexes."""
    db.init()
    with db.get_db() as conn:
        cursor = conn.cursor()
        indexes = cursor.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
        index_names = {i[0] for i in indexes}
        assert "idx_tags_item" in index_names
        assert "idx_tags_tag" in index_names
        assert "idx_checks_item" in index_names


def test_get_db_context_manager(tmp_life_dir):
    """Verify that get_db() provides a valid connection."""
    with db.get_db() as conn:
        assert conn is not None
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1


def test_get_db_auto_commit(tmp_life_dir):
    """Verify that get_db() automatically commits successful transactions."""
    with db.get_db() as conn:
        conn.execute(
            "INSERT INTO items (id, content) VALUES (?, ?)",
            ("test_id", "test content"),
        )

    with db.get_db() as conn:
        result = conn.execute("SELECT content FROM items WHERE id = ?", ("test_id",)).fetchone()
        assert result[0] == "test content"


def test_get_db_auto_rollback(tmp_life_dir):
    """Verify that get_db() automatically rolls back failed transactions."""
    with pytest.raises(sqlite3.IntegrityError):
        with db.get_db() as conn:
            # This will fail because of a NOT NULL constraint
            conn.execute("INSERT INTO items (id) VALUES (?)", ("test_id",))

    with db.get_db() as conn:
        result = conn.execute("SELECT * FROM items WHERE id = ?", ("test_id",)).fetchone()
        assert result is None


def test_db_init(tmp_life_dir):
    db.init()
    assert (tmp_life_dir / "store.db").exists()
