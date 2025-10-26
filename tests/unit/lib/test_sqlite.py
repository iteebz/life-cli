import sqlite3

from life.lib.sqlite import DB_PATH, execute_sql, get_db, init_db


def test_init_db(tmp_life_dir):
    init_db()
    assert (DB_PATH).exists()


def test_init_db_creates_tables(tmp_life_dir):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    assert "items" in tables
    assert "checks" in tables
    assert "item_tags" in tables


def test_init_db_creates_indices(tmp_life_dir):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indices = [row[0] for row in cursor.fetchall()]
    conn.close()

    assert any("item_tags_item" in idx for idx in indices)
    assert any("item_tags_tag" in idx for idx in indices)
    assert any("checks_item" in idx for idx in indices)


def test_execute_sql_select(tmp_life_dir):
    init_db()
    from life.core.item import add_item

    add_item("test")
    result = execute_sql("SELECT COUNT(*) FROM items")
    assert result[0][0] == 1


def test_execute_sql_insert(tmp_life_dir):
    init_db()
    execute_sql("INSERT INTO items (id, content) VALUES ('test-id', 'test content')")
    result = execute_sql("SELECT content FROM items WHERE id = 'test-id'")
    assert result[0][0] == "test content"


def test_get_db_context_manager(tmp_life_dir):
    init_db()

    with get_db() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM items")
        result = cursor.fetchone()[0]
        assert result == 0
