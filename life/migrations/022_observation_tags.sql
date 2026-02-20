ALTER TABLE steward_observations ADD COLUMN tag TEXT;
CREATE INDEX idx_observations_tag ON steward_observations(tag) WHERE tag IS NOT NULL;
