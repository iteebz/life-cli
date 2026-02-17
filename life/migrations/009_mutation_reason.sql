-- 009_mutation_reason.sql
-- Add optional reason field to task_mutations for deferral tracking.

ALTER TABLE task_mutations ADD COLUMN reason TEXT;
