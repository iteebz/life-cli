-- 017_search_fts.sql
-- Full-text search for tasks and habits
-- Uses external content tables to stay in sync with source tables

CREATE VIRTUAL TABLE tasks_fts USING fts5(
    content,
    content='tasks',
    content_rowid='rowid',
    tokenize='porter unicode61'
);

-- Populate FTS table with existing data
INSERT INTO tasks_fts(rowid, content)
SELECT rowid, content FROM tasks;

-- Triggers to keep FTS in sync
CREATE TRIGGER tasks_fts_insert AFTER INSERT ON tasks BEGIN
    INSERT INTO tasks_fts(rowid, content)
    VALUES (NEW.rowid, NEW.content);
END;

CREATE TRIGGER tasks_fts_update AFTER UPDATE ON tasks BEGIN
    UPDATE tasks_fts SET content = NEW.content WHERE rowid = OLD.rowid;
END;

CREATE TRIGGER tasks_fts_delete AFTER DELETE ON tasks BEGIN
    DELETE FROM tasks_fts WHERE rowid = OLD.rowid;
END;

CREATE VIRTUAL TABLE habits_fts USING fts5(
    content,
    content='habits',
    content_rowid='rowid',
    tokenize='porter unicode61'
);

INSERT INTO habits_fts(rowid, content)
SELECT rowid, content FROM habits;

CREATE TRIGGER habits_fts_insert AFTER INSERT ON habits BEGIN
    INSERT INTO habits_fts(rowid, content)
    VALUES (NEW.rowid, NEW.content);
END;

CREATE TRIGGER habits_fts_update AFTER UPDATE ON habits BEGIN
    UPDATE habits_fts SET content = NEW.content WHERE rowid = OLD.rowid;
END;

CREATE TRIGGER habits_fts_delete AFTER DELETE ON habits BEGIN
    DELETE FROM habits_fts WHERE rowid = OLD.rowid;
END;

CREATE VIRTUAL TABLE tags_fts USING fts5(
    tag,
    content='tags',
    content_rowid='rowid',
    tokenize='porter unicode61'
);

INSERT INTO tags_fts(rowid, tag)
SELECT rowid, tag FROM tags;

CREATE TRIGGER tags_fts_insert AFTER INSERT ON tags BEGIN
    INSERT INTO tags_fts(rowid, tag)
    VALUES (NEW.rowid, NEW.tag);
END;

CREATE TRIGGER tags_fts_update AFTER UPDATE ON tags BEGIN
    UPDATE tags_fts SET tag = NEW.tag WHERE rowid = OLD.rowid;
END;

CREATE TRIGGER tags_fts_delete AFTER DELETE ON tags BEGIN
    DELETE FROM tags_fts WHERE rowid = OLD.rowid;
END;
