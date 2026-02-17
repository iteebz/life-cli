-- 006_task_mutations.sql
-- Record every field mutation on a task: what changed, from what, to what, when.

CREATE TABLE task_mutations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    field TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    mutated_at TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%S', 'now'))
);

CREATE INDEX idx_mutations_task ON task_mutations(task_id);
CREATE INDEX idx_mutations_field ON task_mutations(field);
CREATE INDEX idx_mutations_at ON task_mutations(mutated_at);
