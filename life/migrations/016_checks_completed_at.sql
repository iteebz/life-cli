-- 016_checks_completed_at.sql
-- Add completed_at timestamp to checks table for time tracking
-- Migrate existing check_date values to completed_at (midnight)

BEGIN;

-- Create new table with completed_at
CREATE TABLE checks_new (
    habit_id TEXT NOT NULL,
    check_date TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    PRIMARY KEY (habit_id, check_date),
    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
    CHECK (DATE(check_date) IS NOT NULL),
    CHECK (DATETIME(completed_at) IS NOT NULL)
);

-- Migrate existing data: convert check_date to midnight timestamp
INSERT INTO checks_new (habit_id, check_date, completed_at)
SELECT habit_id, check_date, check_date || 'T00:00:00'
FROM checks;

-- Drop old table and rename new one
DROP TABLE checks;
ALTER TABLE checks_new RENAME TO checks;

-- Recreate index
CREATE INDEX idx_checks_date ON checks(check_date);

COMMIT;
