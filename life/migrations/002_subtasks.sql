-- 002_subtasks.sql
-- Add parent_id to tasks for one-level subtask hierarchy.

PRAGMA foreign_keys = ON;

ALTER TABLE tasks ADD COLUMN parent_id TEXT REFERENCES tasks(id) ON DELETE CASCADE;

CREATE INDEX idx_tasks_parent ON tasks(parent_id) WHERE parent_id IS NOT NULL;
