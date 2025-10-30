-- 001_foundation.sql
-- Canonical schema: Tasks (one-shot) and Habits (daily repeating).
-- Type distinction via separate tables, not polymorphic flags.
-- Tags are user-facing metadata with exclusive-or FK constraint.

PRAGMA foreign_keys = ON;

CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    focus BOOLEAN DEFAULT 0,
    due_date TEXT,
    created TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%S', 'now')),
    completed TEXT,
    CHECK (length(content) > 0),
    CHECK (due_date IS NULL OR DATE(due_date) IS NOT NULL),
    CHECK (completed IS NULL OR DATE(completed) IS NOT NULL)
);

CREATE TABLE habits (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    created TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%S', 'now')),
    CHECK (length(content) > 0)
);

CREATE TABLE checks (
    habit_id TEXT NOT NULL,
    check_date TEXT NOT NULL,
    PRIMARY KEY (habit_id, check_date),
    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
    CHECK (DATE(check_date) IS NOT NULL)
);

CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    habit_id TEXT,
    tag TEXT NOT NULL,
    CHECK (length(tag) > 0),
    CHECK ((task_id IS NOT NULL AND habit_id IS NULL) OR (task_id IS NULL AND habit_id IS NOT NULL)),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
    UNIQUE(task_id, habit_id, tag)
);

CREATE INDEX idx_tasks_due ON tasks(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX idx_tasks_completed ON tasks(completed) WHERE completed IS NOT NULL;
CREATE INDEX idx_tasks_focus ON tasks(focus) WHERE focus = 1;
CREATE INDEX idx_habits_created ON habits(created);
CREATE INDEX idx_checks_date ON checks(check_date);
CREATE INDEX idx_tags_task ON tags(task_id);
CREATE INDEX idx_tags_habit ON tags(habit_id);
CREATE INDEX idx_tags_name ON tags(tag);
