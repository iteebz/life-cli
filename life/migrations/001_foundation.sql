-- 001_foundation.sql
-- Flattened schema from all migrations.

PRAGMA foreign_keys = ON;

CREATE TABLE items (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    focus BOOLEAN DEFAULT 0,
    due_date TEXT NULL,
    created TEXT DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%S', 'now')),
    completed TEXT NULL,
    is_habit BOOLEAN NOT NULL DEFAULT 0,
    CHECK (is_habit = 0 OR due_date IS NULL),
    CHECK (is_habit = 0 OR focus = 0)
);

CREATE TABLE checks (
    item_id TEXT NOT NULL,
    check_date TEXT NOT NULL,
    PRIMARY KEY (item_id, check_date),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

CREATE TABLE tags (
    item_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (item_id, tag),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

DROP TRIGGER IF EXISTS checks_require_repeat_on_insert;
CREATE TRIGGER checks_require_repeat_on_insert
BEFORE INSERT ON checks
FOR EACH ROW
BEGIN
    SELECT
        CASE
            WHEN COALESCE((SELECT is_habit FROM items WHERE id = NEW.item_id), 0) = 1
                THEN NULL
            ELSE RAISE(ABORT, 'checks require habit item')
        END;
END;

DROP TRIGGER IF EXISTS checks_require_repeat_on_update;
CREATE TRIGGER checks_require_repeat_on_update
BEFORE UPDATE OF item_id ON checks
FOR EACH ROW
BEGIN
    SELECT
        CASE
            WHEN COALESCE((SELECT is_habit FROM items WHERE id = NEW.item_id), 0) = 1
                THEN NULL
            ELSE RAISE(ABORT, 'checks require habit item')
        END;
END;

DROP TRIGGER IF EXISTS prevent_repeat_toggle_with_checks;
CREATE TRIGGER prevent_repeat_toggle_with_checks
BEFORE UPDATE OF is_habit ON items
FOR EACH ROW
WHEN NEW.is_habit = 0 AND OLD.is_habit != 0
BEGIN
    SELECT
        CASE
            WHEN EXISTS (SELECT 1 FROM checks WHERE item_id = OLD.id) THEN
                RAISE(ABORT, 'cannot unset habit while checks exist')
            ELSE NULL
        END;
END;

CREATE INDEX IF NOT EXISTS idx_items_due_date ON items(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_items_completed ON items(completed) WHERE completed IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_checks_item ON checks(item_id);
CREATE INDEX IF NOT EXISTS idx_tags_item ON tags(item_id);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);