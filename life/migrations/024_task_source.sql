-- 024_task_source.sql
-- Track provenance of steward tasks: who initiated them.
-- Values: 'tyson' (human-requested), 'steward' (self-generated), 'scheduled' (cron/autonomous)
-- NULL = non-steward task (Tyson's tasks, not relevant)

ALTER TABLE tasks ADD COLUMN source TEXT CHECK (source IS NULL OR source IN ('tyson', 'steward', 'scheduled'));
