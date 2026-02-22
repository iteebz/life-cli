ALTER TABLE tasks RENAME COLUMN due_date TO scheduled_date;
ALTER TABLE tasks RENAME COLUMN due_time TO scheduled_time;
ALTER TABLE tasks ADD COLUMN deadline_date TEXT CHECK (deadline_date IS NULL OR DATE(deadline_date) IS NOT NULL);
ALTER TABLE tasks ADD COLUMN deadline_time TEXT CHECK (deadline_time IS NULL OR TIME(deadline_time) IS NOT NULL);
