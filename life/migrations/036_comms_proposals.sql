CREATE TABLE proposals (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    proposed_action TEXT NOT NULL,
    agent_reasoning TEXT,
    proposed_by TEXT DEFAULT 'agent',
    proposed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    approved_at TIMESTAMP,
    approved_by TEXT,
    user_reasoning TEXT,
    
    executed_at TIMESTAMP,
    rejected_at TIMESTAMP,
    
    status TEXT DEFAULT 'pending'
);

CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_proposals_entity ON proposals(entity_type, entity_id);
