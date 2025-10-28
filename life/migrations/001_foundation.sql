-- 001_foundation.sql
-- Baseline schema snapshot reflecting the current production state.

CREATE TABLE items (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    focus BOOLEAN DEFAULT 0,
    due DATE NULL,
    created INTEGER DEFAULT (CAST(CURRENT_TIMESTAMP AS REAL)),
    completed DATE NULL,
    is_repeat BOOLEAN DEFAULT 0
);

CREATE TABLE checks (
    item_id TEXT NOT NULL,
    check_date DATE NOT NULL,
    PRIMARY KEY (item_id, check_date),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

CREATE TABLE tags (
    item_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (item_id, tag),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

CREATE INDEX idx_items_due ON items(due);
CREATE INDEX idx_items_completed ON items(completed);
CREATE INDEX idx_checks_item ON checks(item_id);
CREATE INDEX idx_tags_item ON tags(item_id);
CREATE INDEX idx_tags_tag ON tags(tag);
