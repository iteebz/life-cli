ALTER TABLE tasks ADD COLUMN is_deadline INTEGER NOT NULL DEFAULT 0;
UPDATE tasks SET scheduled_date = COALESCE(deadline_date, scheduled_date), scheduled_time = COALESCE(deadline_time, scheduled_time), is_deadline = 1 WHERE deadline_date IS NOT NULL OR deadline_time IS NOT NULL;
ALTER TABLE tasks DROP COLUMN deadline_date;
ALTER TABLE tasks DROP COLUMN deadline_time;
