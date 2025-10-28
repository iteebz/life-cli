-- 002_canonical.sql
-- Enforce canonical invariants for repeat items and checks.

BEGIN;

-- 1. Remove orphaned rows introduced by previous schema experiments.
DELETE FROM checks
WHERE item_id NOT IN (SELECT id FROM items);

DELETE FROM tags
WHERE item_id NOT IN (SELECT id FROM items);

-- Ensure every item that already has checks is marked as repeat.
UPDATE items
SET is_repeat = 1
WHERE id IN (SELECT item_id FROM checks);

-- 2. Strengthen runtime invariants with triggers.
DROP TRIGGER IF EXISTS checks_require_repeat_on_insert;

CREATE TRIGGER checks_require_repeat_on_insert
BEFORE INSERT ON checks
FOR EACH ROW
BEGIN
    SELECT
        CASE
            WHEN COALESCE((SELECT is_repeat FROM items WHERE id = NEW.item_id), 0) = 1
                THEN NULL
            ELSE RAISE(ABORT, 'checks require repeat item')
        END;
END;

DROP TRIGGER IF EXISTS checks_require_repeat_on_update;

CREATE TRIGGER checks_require_repeat_on_update
BEFORE UPDATE OF item_id ON checks
FOR EACH ROW
BEGIN
    SELECT
        CASE
            WHEN COALESCE((SELECT is_repeat FROM items WHERE id = NEW.item_id), 0) = 1
                THEN NULL
            ELSE RAISE(ABORT, 'checks require repeat item')
        END;
END;

DROP TRIGGER IF EXISTS prevent_repeat_toggle_with_checks;

CREATE TRIGGER prevent_repeat_toggle_with_checks
BEFORE UPDATE OF is_repeat ON items
FOR EACH ROW
WHEN NEW.is_repeat = 0 AND OLD.is_repeat != 0
BEGIN
    SELECT
        CASE
            WHEN EXISTS (SELECT 1 FROM checks WHERE item_id = OLD.id) THEN
                RAISE(ABORT, 'cannot unset repeat while checks exist')
            ELSE NULL
        END;
END;

-- 3. Helpful filtered index for repeat lookups.
CREATE INDEX IF NOT EXISTS idx_items_repeat ON items(id) WHERE is_repeat = 1;

-- Replace legacy wide indexes with filtered variants.
DROP INDEX IF EXISTS idx_items_due;
DROP INDEX IF EXISTS idx_items_completed;

CREATE INDEX IF NOT EXISTS idx_items_due ON items(due) WHERE due IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_items_completed ON items(completed) WHERE completed IS NOT NULL;

COMMIT;
