-- 011_deleted_tasks.sql
-- Audit log for deleted tasks. Written before hard DELETE so data survives CASCADE.

CREATE TABLE deleted_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT,
    deleted_at TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%S', 'now'))
);

CREATE INDEX idx_deleted_tasks_at ON deleted_tasks(deleted_at);
