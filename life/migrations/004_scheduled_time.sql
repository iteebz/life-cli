-- 004_scheduled_time.sql
-- Add scheduled_time (HH:MM) to tasks for intra-day ordering.

ALTER TABLE tasks ADD COLUMN scheduled_time TEXT CHECK (scheduled_time IS NULL OR TIME(scheduled_time) IS NOT NULL);
