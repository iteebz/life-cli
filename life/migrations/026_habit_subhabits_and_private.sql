ALTER TABLE habits ADD COLUMN parent_id TEXT REFERENCES habits(id) ON DELETE CASCADE;
ALTER TABLE habits ADD COLUMN private BOOLEAN NOT NULL DEFAULT 0;
CREATE INDEX idx_habits_parent ON habits(parent_id) WHERE parent_id IS NOT NULL;
