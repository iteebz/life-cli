ALTER TABLE deleted_tasks ADD COLUMN cancel_reason TEXT;
ALTER TABLE deleted_tasks ADD COLUMN cancelled INTEGER NOT NULL DEFAULT 0;
