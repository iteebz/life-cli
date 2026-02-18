-- 012_task_links.sql
-- Free-form links between any two tasks. Bidirectional by convention.

CREATE TABLE task_links (
    from_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    to_id   TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    PRIMARY KEY (from_id, to_id)
);

CREATE INDEX idx_task_links_to ON task_links(to_id);
