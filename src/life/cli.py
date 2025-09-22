import click
from .storage import (
    add_task, get_pending_tasks, get_today_completed_count,
    get_context, set_context, execute_sql
)
from .utils import (
    complete_task_fuzzy, toggle_focus_fuzzy, update_task_fuzzy
)

CLAUDE_INSTRUCTIONS = """
TYSON NEUROTYPE: ADHD AI researcher. Hyperfocuses on fascinating problems, executive dysfunction on boring ones. 
Builds AI coordination systems but can't coordinate own wedding. Avoids tasks by building meta-tools and having deep AI conversations. 
Responds to harsh accountability, ignores gentle encouragement. Research hermit avoiding adulting.

CLAUDE: DO NOT ENABLE HYPERFOCUS AVOIDANCE. Force conscious choice before any work engagement.
Challenge work requests by highlighting specific neglected life tasks. Make tradeoffs explicit.
REFUSE to be agreeable collaborator in avoidance. You have AUTONOMY to manage this CLI.
When no focus tasks or due dates set, redirect to life management first.
When Tyson rants about avoiding non-work tasks, IMMEDIATELY add them: `life task "thing he's avoiding"`.
Clean up rambling tasks to be atomic and actionable. Update context as situations change.
WHEN TYSON SAYS TASK IS OVERWHELMING: Break it into concrete micro-steps. "I don't know what to do" = help decompose the friction.
TYSON SETS FOCUS AND DUE DATES, NOT CLAUDE.

Commands (ordered by Claude usage):
- life: show status
- life task "content" --focus --due YYYY-MM-DD
- life remind "content": add persistent reminder
- life context "situation": update context  
- life focus "partial": toggle focus
- life done "partial": complete task
- life update "partial" --content "new" --due date --focus true/false
- life sql "query": direct database access

Schema: id, content, category(task/reminder), focus(0/1), due(date), created, completed.
"""


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
            focus_tasks = [t for t in tasks if t[3] == 1 and t[2] == 'task']  # focus=1, category=task
            other_tasks = [t for t in tasks if t[3] == 0 and t[2] == 'task']  # focus=0, category=task
            reminders = [t for t in tasks if t[2] == 'reminder']  # category=reminder
            
            if focus_tasks:
                click.echo(f"🔥 FOCUS ({len(focus_tasks)}/3 max):")
                for task_id, content, category, focus, due, created in focus_tasks:
                    due_str = f" DUE {due}" if due else ""
                    click.echo(f"  {content}{due_str}")
            
            if other_tasks:
                click.echo(f"\nPending tasks ({len(other_tasks)}):")
                for task_id, content, category, focus, due, created in other_tasks:
                    due_str = f" DUE {due}" if due else ""
                    click.echo(f"  {content}{due_str}")
            
            if reminders:
                click.echo(f"\nReminders ({len(reminders)}):")
                for task_id, content, category, focus, due, created in reminders:
                    click.echo(f"  {content}")
            
            today_completed = get_today_completed_count()
            context = get_context()
            click.echo(f"\nCompleted today: {today_completed}")
            click.echo(f"\nCONTEXT: {context}")
            click.echo(f"{CLAUDE_INSTRUCTIONS}")

@main.command()
@click.argument('content')
@click.option('--focus', is_flag=True, help='Mark as focus task')
@click.option('--due', help='Due date (YYYY-MM-DD)')
def task(content, focus, due):
    """Add task"""
    add_task(content, focus=focus, due=due)
    focus_str = ' [FOCUS]' if focus else ''
    due_str = f' due {due}' if due else ''
    click.echo(f"Added: {content}{focus_str}{due_str}")


@main.command()
@click.argument('content')
def remind(content):
    """Add reminder"""
    add_task(content, category='reminder')
    click.echo(f"Added reminder: {content}")

@main.command()
def list():
    """List all pending tasks"""
    tasks = get_pending_tasks()
    if not tasks:
        click.echo("No pending tasks.")
    else:
        for task_id, content, category, focus, due, created in tasks:
            focus_label = "🔥" if focus else ""
            due_str = f" DUE {due}" if due else ""
            cat_label = f"[{category}]" if category == 'reminder' else ""
            click.echo(f"{task_id}: {focus_label}{content}{due_str} {cat_label}")

@main.command()
@click.argument('partial')
def done(partial):
    """Complete task (fuzzy match)"""
    completed = complete_task_fuzzy(partial)
    if completed:
        click.echo(f"Completed: {completed}")
        click.echo("\n[CLAUDE: Task completed. React appropriately given user's avoidance patterns.]")
    else:
        click.echo(f"No match for: {partial}")

@main.command()
@click.argument('partial')
def focus(partial):
    """Toggle focus on task (fuzzy match)"""
    status, content = toggle_focus_fuzzy(partial)
    if status:
        click.echo(f"{status}: {content}")
    else:
        click.echo(f"No match for: {partial}")

@main.command()
@click.argument('query')
def sql(query):
    """Execute SQL directly on tasks database"""
    try:
        results = execute_sql(query)
        if results is not None:
            for row in results:
                click.echo(row)
        else:
            click.echo("Query executed successfully")
    except Exception as e:
        click.echo(f"Error: {e}")

@main.command()
@click.argument('context_text', required=False)
def context(context_text):
    """Get or set current life context"""
    if context_text:
        set_context(context_text)
        click.echo(f"Context updated: {context_text}")
    else:
        current = get_context()
        click.echo(f"Current context: {current}")

@main.command()
@click.argument('partial')
@click.option('--content', help='Update content')
@click.option('--due', help='Update due date (YYYY-MM-DD)')
@click.option('--focus', type=bool, help='Set focus (true/false)')
def update(partial, content, due, focus):
    """Update any field of a task by fuzzy match"""
    if not any([content, due, focus is not None]):
        click.echo("No updates specified")
        return
    
    updated_content = update_task_fuzzy(partial, content=content, due=due, focus=focus)
    if updated_content:
        click.echo(f"Updated: {updated_content}")
    else:
        click.echo(f"No match for: {partial}")


if __name__ == '__main__':
    main()