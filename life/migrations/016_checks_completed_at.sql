-- 016_checks_completed_at.sql
-- Add completed_at timestamp to checks table for time tracking
-- Migrate existing check_date values to completed_at (midnight)

BEGIN;

-- Add the new column
ALTER TABLE checks ADD COLUMN completed_at TEXT;

-- Migrate existing data: convert check_date to midnight timestamp
UPDATE checks 
SET completed_at = check_date || 'T00:00:00' 
WHERE completed_at IS NULL;

-- Make the column NOT NULL after migration
ALTER TABLE checks ALTER COLUMN completed_at TEXT NOT NULL;

-- Add constraint to ensure valid timestamps
ALTER TABLE checks ADD COLUMN check_completed_at_ok CHECK (completed_at IS NULL OR DATETIME(completed_at) IS NOT NULL);

COMMIT;
