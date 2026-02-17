CREATE TABLE IF NOT EXISTS interventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    description TEXT NOT NULL,
    result TEXT NOT NULL CHECK (result IN ('won', 'lost', 'deferred')),
    note TEXT
);
