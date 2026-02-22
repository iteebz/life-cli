-- Sender statistics for priority scoring
CREATE TABLE IF NOT EXISTS sender_stats (
    id TEXT PRIMARY KEY,
    sender TEXT NOT NULL UNIQUE,
    received_count INTEGER DEFAULT 0,
    replied_count INTEGER DEFAULT 0,
    archived_count INTEGER DEFAULT 0,
    deleted_count INTEGER DEFAULT 0,
    flagged_count INTEGER DEFAULT 0,
    avg_response_hours REAL,
    last_received_at TEXT,
    last_action_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sender_stats_sender ON sender_stats(sender);
