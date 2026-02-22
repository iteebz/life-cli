DROP TABLE IF EXISTS threads;
DROP INDEX IF EXISTS idx_threads_account;
DROP INDEX IF EXISTS idx_threads_needs_reply;

-- drafts no longer reference thread_id (remove FK constraint by recreating table)
CREATE TABLE drafts_new (
    id TEXT PRIMARY KEY,
    thread_id TEXT,
    to_addr TEXT NOT NULL,
    cc_addr TEXT,
    subject TEXT,
    body TEXT NOT NULL,
    claude_reasoning TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    sent_at TIMESTAMP
);

INSERT INTO drafts_new SELECT id, thread_id, to_addr, cc_addr, subject, body, claude_reasoning, created_at, approved_at, sent_at FROM drafts;
DROP TABLE drafts;
ALTER TABLE drafts_new RENAME TO drafts;

CREATE INDEX idx_drafts_approved ON drafts(approved_at);
