ALTER TABLE audit_log ADD COLUMN proposed_action TEXT;
ALTER TABLE audit_log ADD COLUMN user_decision TEXT;
ALTER TABLE audit_log ADD COLUMN reasoning TEXT;
