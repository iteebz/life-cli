CREATE TABLE IF NOT EXISTS signal_messages (
    id TEXT PRIMARY KEY,
    account_phone TEXT NOT NULL,
    sender_phone TEXT NOT NULL,
    sender_name TEXT,
    body TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    group_id TEXT,
    received_at TEXT NOT NULL,
    read_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_signal_messages_account ON signal_messages(account_phone);
CREATE INDEX IF NOT EXISTS idx_signal_messages_sender ON signal_messages(sender_phone);
CREATE INDEX IF NOT EXISTS idx_signal_messages_timestamp ON signal_messages(timestamp DESC);
