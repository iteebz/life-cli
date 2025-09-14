import sqlite3
import click
from pathlib import Path
from datetime import datetime
from difflib import get_close_matches

DB_PATH = Path.home() / ".life.db"

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            type TEXT DEFAULT 'task',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP NULL
        )
    """)
    conn.commit()
    conn.close()

def add_task(content, task_type='task'):
    """Add task to database"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO tasks (content, type) VALUES (?, ?)", (content, task_type))
    conn.commit()
    conn.close()

def get_pending_tasks():
    """Get all pending tasks"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT id, content, type, created_at 
        FROM tasks 
        WHERE completed_at IS NULL 
        ORDER BY type, created_at DESC
    """)
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def complete_task_fuzzy(partial):
    """Complete task using fuzzy matching"""
    pending = get_pending_tasks()
    if not pending:
        return None
    
    # Extract just the content for matching
    contents = [task[1] for task in pending]
    matches = get_close_matches(partial.lower(), [c.lower() for c in contents], n=1, cutoff=0.3)
    
    if not matches:
        return None
    
    # Find the original task
    match_content = matches[0]
    for task in pending:
        if task[1].lower() == match_content:
            # Mark as completed
            init_db()
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "UPDATE tasks SET completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (task[0],)
            )
            conn.commit()
            conn.close()
            return task[1]
    
    return None

def clear_all_tasks():
    """Delete all tasks"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM tasks")
    conn.commit()
    conn.close()

@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """ADHD executive function rescue system"""
    if ctx.invoked_subcommand is None:
        # Default: show pending tasks
        tasks = get_pending_tasks()
        if not tasks:
            click.echo("No pending tasks. You're either productive or fucked.")
        else:
            task_items = [t for t in tasks if t[2] == 'task']
            reminder_items = [t for t in tasks if t[2] == 'reminder']
            
            if task_items:
                click.echo(f"Pending tasks ({len(task_items)}):")
                for task_id, content, task_type, created in task_items:
                    date = datetime.fromisoformat(created).strftime("%m-%d")
                    click.echo(f"  {task_id}: {content} ({date})")
            
            if reminder_items:
                click.echo(f"\nReminders ({len(reminder_items)}):")
                for task_id, content, task_type, created in reminder_items:
                    date = datetime.fromisoformat(created).strftime("%m-%d")
                    click.echo(f"  {task_id}: {content} ({date})")
            
            click.echo("\n[CLAUDE: Assess neglect patterns and deliver aggressive executive function intervention. Wedding Nov 15. Time-sensitive items need immediate action. User responds to being sworn at and direct accountability. Check context clues for hermit behavior.]")

@main.command()
@click.argument('content')
def add(content):
    """Add task"""
    add_task(content)
    click.echo(f"Added: {content}")

@main.command()
@click.argument('content')
def remind(content):
    """Add reminder"""
    add_task(content, 'reminder')
    click.echo(f"Added reminder: {content}")

@main.command()
def list():
    """List all pending tasks"""
    tasks = get_pending_tasks()
    if not tasks:
        click.echo("No pending tasks.")
    else:
        for task_id, content, task_type, created in tasks:
            date = datetime.fromisoformat(created).strftime("%m-%d %H:%M")
            type_label = f"[{task_type}]" if task_type == 'reminder' else ""
            click.echo(f"{task_id}: {content} {type_label} ({date})")

@main.command()
@click.argument('partial')
def done(partial):
    """Complete task (fuzzy match)"""
    completed = complete_task_fuzzy(partial)
    if completed:
        click.echo(f"Completed: {completed}")
    else:
        click.echo(f"No match for: {partial}")

@main.command()
@click.confirmation_option(prompt="Delete all tasks?")
def clear():
    """Delete all tasks"""
    clear_all_tasks()
    click.echo("All tasks deleted.")

if __name__ == '__main__':
    main()