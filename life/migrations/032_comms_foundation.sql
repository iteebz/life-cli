CREATE TABLE accounts (
    id TEXT PRIMARY KEY,
    service_type TEXT NOT NULL,
    provider TEXT NOT NULL,
    email TEXT NOT NULL,
    auth_data TEXT,
    enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider, email)
);

CREATE TABLE threads (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    subject TEXT,
    participants TEXT NOT NULL,
    last_message_at TIMESTAMP,
    needs_reply INTEGER DEFAULT 0,
    last_seen_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

CREATE TABLE drafts (
    id TEXT PRIMARY KEY,
    thread_id TEXT,
    to_addr TEXT NOT NULL,
    cc_addr TEXT,
    subject TEXT,
    body TEXT NOT NULL,
    claude_reasoning TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    sent_at TIMESTAMP,
    FOREIGN KEY (thread_id) REFERENCES threads(id)
);

CREATE TABLE send_queue (
    id TEXT PRIMARY KEY,
    draft_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    scheduled_at TIMESTAMP,
    attempts INTEGER DEFAULT 0,
    last_error TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (draft_id) REFERENCES drafts(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    metadata TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    condition TEXT NOT NULL,
    action TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_threads_account ON threads(account_id);
CREATE INDEX idx_threads_needs_reply ON threads(needs_reply);
CREATE INDEX idx_drafts_approved ON drafts(approved_at);
CREATE INDEX idx_send_queue_status ON send_queue(status);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
