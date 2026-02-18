-- 013_task_links_created_at.sql
-- Track when links were created to enable links-per-day metrics.

ALTER TABLE task_links ADD COLUMN created_at TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%S', 'now'));
