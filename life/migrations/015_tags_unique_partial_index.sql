CREATE UNIQUE INDEX IF NOT EXISTS idx_tags_task_unique ON tags(task_id, tag) WHERE task_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_tags_habit_unique ON tags(habit_id, tag) WHERE habit_id IS NOT NULL;
