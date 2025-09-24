import sqlite3
from pathlib import Path
from datetime import datetime

LIFE_DIR = Path.home() / ".life"
DB_PATH = LIFE_DIR / "store.db"
CONTEXT_PATH = LIFE_DIR / "context.md"


def init_db():
    """Initialize SQLite database"""
    LIFE_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'task',
            focus BOOLEAN DEFAULT 0,
            due DATE NULL,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed TIMESTAMP NULL
        )
    """)
    conn.commit()
    conn.close()


def add_task(content, category='task', focus=False, due=None):
    """Add task to database"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO tasks (content, category, focus, due) VALUES (?, ?, ?, ?)", 
                (content, category, focus, due))
    conn.commit()
    conn.close()


def get_pending_tasks():
    """Get all pending tasks ordered by focus and due date"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT id, content, category, focus, due, created 
        FROM tasks 
        WHERE completed IS NULL 
        ORDER BY focus DESC, due ASC NULLS LAST, created ASC
    """)
    tasks = cursor.fetchall()
    conn.close()
    return tasks


def get_today_completed_count():
    """Get count of tasks completed today"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT COUNT(*) 
        FROM tasks 
        WHERE DATE(completed) = DATE('now', 'localtime')
    """)
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_weekly_momentum():
    """Get weekly completion stats for this week and last week"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    
    # This week completed
    cursor = conn.execute("""
        SELECT COUNT(*) 
        FROM tasks 
        WHERE completed IS NOT NULL 
        AND completed >= DATE('now', 'localtime', 'weekday 0', '-6 days')
    """)
    this_week_completed = cursor.fetchone()[0]
    
    # This week added
    cursor = conn.execute("""
        SELECT COUNT(*) 
        FROM tasks 
        WHERE created >= DATE('now', 'localtime', 'weekday 0', '-6 days')
    """)
    this_week_added = cursor.fetchone()[0]
    
    # Last week completed
    cursor = conn.execute("""
        SELECT COUNT(*) 
        FROM tasks 
        WHERE completed IS NOT NULL 
        AND completed >= DATE('now', 'localtime', 'weekday 0', '-13 days')
        AND completed < DATE('now', 'localtime', 'weekday 0', '-6 days')
    """)
    last_week_completed = cursor.fetchone()[0]
    
    # Last week added
    cursor = conn.execute("""
        SELECT COUNT(*) 
        FROM tasks 
        WHERE created >= DATE('now', 'localtime', 'weekday 0', '-13 days')
        AND created < DATE('now', 'localtime', 'weekday 0', '-6 days')
    """)
    last_week_added = cursor.fetchone()[0]
    
    conn.close()
    return this_week_completed, this_week_added, last_week_completed, last_week_added


def complete_task(task_id):
    """Mark task as completed"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE tasks SET completed = CURRENT_TIMESTAMP WHERE id = ?",
        (task_id,)
    )
    conn.commit()
    conn.close()


def update_task(task_id, content=None, due=None, focus=None):
    """Update task fields"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    
    updates = []
    params = []
    
    if content is not None:
        updates.append("content = ?")
        params.append(content)
    if due is not None:
        updates.append("due = ?")
        params.append(due)
    if focus is not None:
        updates.append("focus = ?")
        params.append(1 if focus else 0)
    
    if updates:
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        params.append(task_id)
        conn.execute(query, params)
        conn.commit()
    
    conn.close()


def toggle_focus(task_id, current_focus):
    """Toggle focus status of task"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    new_focus = 1 if current_focus == 0 else 0
    conn.execute("UPDATE tasks SET focus = ? WHERE id = ?", (new_focus, task_id))
    conn.commit()
    conn.close()
    return new_focus


def execute_sql(query):
    """Execute arbitrary SQL query"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        if query.strip().upper().startswith('SELECT'):
            cursor = conn.execute(query)
            results = cursor.fetchall()
            return results
        else:
            conn.execute(query)
            conn.commit()
            return None
    finally:
        conn.close()


def get_context():
    """Get current life context"""
    if CONTEXT_PATH.exists():
        return CONTEXT_PATH.read_text().strip()
    return "No context set"


def set_context(context):
    """Set current life context"""
    LIFE_DIR.mkdir(exist_ok=True)
    CONTEXT_PATH.write_text(context)


def clear_all_tasks():
    """Delete all tasks"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM tasks")
    conn.commit()
    conn.close()