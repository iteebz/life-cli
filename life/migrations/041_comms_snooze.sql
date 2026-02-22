-- Snooze tracking for deferred items
CREATE TABLE IF NOT EXISTS snoozed_items (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    source_id TEXT,
    snooze_until TEXT NOT NULL,
    reason TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    resurfaced_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_snoozed_until ON snoozed_items(snooze_until);
CREATE INDEX IF NOT EXISTS idx_snoozed_entity ON snoozed_items(entity_type, entity_id);
