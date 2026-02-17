PRAGMA foreign_keys = OFF;

CREATE TABLE tasks_new (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    focus BOOLEAN DEFAULT 0,
    due_date TEXT,
    created TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%S', 'now')),
    completed_at TEXT,
    parent_id TEXT REFERENCES tasks_new(id) ON DELETE CASCADE,
    CHECK (length(content) > 0),
    CHECK (due_date IS NULL OR DATE(due_date) IS NOT NULL)
);

INSERT INTO tasks_new SELECT id, content, focus, due_date, created, completed, parent_id FROM tasks;

DROP TABLE tasks;
ALTER TABLE tasks_new RENAME TO tasks;

CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_completed_at ON tasks(completed_at) WHERE completed_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_focus ON tasks(focus) WHERE focus = 1;
CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_id) WHERE parent_id IS NOT NULL;

PRAGMA foreign_keys = ON;
