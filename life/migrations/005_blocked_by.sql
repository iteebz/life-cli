-- 005_blocked_by.sql
-- One-way pointer: task B is blocked by task A.
-- Only tasks block tasks. NULL = not blocked.

ALTER TABLE tasks ADD COLUMN blocked_by TEXT REFERENCES tasks(id) ON DELETE SET NULL;

CREATE INDEX idx_tasks_blocked_by ON tasks(blocked_by) WHERE blocked_by IS NOT NULL;
