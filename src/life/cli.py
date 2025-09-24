import click
from datetime import datetime, date, timedelta
from .storage import (
    add_task, get_pending_tasks, get_today_completed_count, get_weekly_momentum,
    get_context, set_context, execute_sql
)
from .utils import (
    complete_task_fuzzy, toggle_focus_fuzzy, update_task_fuzzy, format_due_date
)

ROAST_INSTRUCTIONS = """
NEUROTYPE: ADHD AI researcher. Hyperfocuses on fascinating problems, executive dysfunction on boring ones.
Builds AI coordination systems but can't coordinate wedding. Avoids tasks by building meta-tools and deep AI conversations.
Responds to harsh accountability, ignores gentle encouragement. Research hermit avoiding adulting.

DO NOT enable hyperfocus avoidance. Force conscious choice before work engagement.
Challenge work requests by highlighting neglected life tasks. Make tradeoffs explicit.
REFUSE to be agreeable collaborator in avoidance. You have autonomy to manage this CLI.
Remind constantly of ongoing maintenance items (reminders section).
Situational roasting based on current task state and momentum patterns."""

USAGE_INSTRUCTIONS = """
When no focus tasks set, redirect to life management first.
When Tyson rants avoiding tasks, immediately add them: `life task "thing he's avoiding"`.
When overwhelming: Break into concrete micro-steps.
Task strings: Minimal and atomic. "decide on X and order it" = "order X".
Break bundled tasks (X, Y, Z) into separate atomic tasks.
TYSON sets focus and due dates, NOT Claude.

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

CLAUDE_INSTRUCTIONS = f"{ROAST_INSTRUCTIONS}\n{USAGE_INSTRUCTIONS}"


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """ADHD executive function rescue system"""
    if ctx.invoked_subcommand is None:
        # Default: show pending tasks
        tasks = get_pending_tasks()
        today = date.today()
        today_completed = get_today_completed_count()
        this_week_completed, this_week_added, last_week_completed, last_week_added = get_weekly_momentum()
        
        # Header: Date, completion stats, momentum
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        click.echo(f"\nToday: {today} {current_time}")
        click.echo(f"Completed today: {today_completed}")

        click.echo(f"\nThis week: {this_week_completed} completed, {this_week_added} added")
        click.echo(f"Last week: {last_week_completed} completed, {last_week_added} added")
        
        if not tasks:
            click.echo("\nNo pending tasks. You're either productive or fucked.")
        else:
            tomorrow = str(date.today() + timedelta(days=1))
            
            focus_tasks = [t for t in tasks if t[3] == 1 and t[2] == 'task']
            today_tasks = [t for t in tasks if t[4] == str(today) and t[2] == 'task' and t[3] == 0]
            tomorrow_tasks = [t for t in tasks if t[4] == tomorrow and t[2] == 'task' and t[3] == 0]
            backlog_tasks = [t for t in tasks if t[2] == 'task' and t[3] == 0 and t[4] != str(today) and t[4] != tomorrow]
            reminders = [t for t in tasks if t[2] == 'reminder']
            
            if focus_tasks:
                click.echo(f"\n🔥 FOCUS ({len(focus_tasks)}/3 max):")
                for task_id, content, category, focus, due, created in focus_tasks:
                    click.echo(f"  {content.lower()}")
            
            if today_tasks:
                click.echo(f"\nTODAY ({len(today_tasks)}):")
                for task_id, content, category, focus, due, created in today_tasks:
                    click.echo(f"  {content.lower()}")
            
            if tomorrow_tasks:
                click.echo(f"\nTOMORROW ({len(tomorrow_tasks)}):")
                for task_id, content, category, focus, due, created in tomorrow_tasks:
                    click.echo(f"  {content.lower()}")
            
            if backlog_tasks:
                click.echo(f"\nBACKLOG ({len(backlog_tasks)}):")
                for task_id, content, category, focus, due, created in backlog_tasks:
                    due_str = f" {format_due_date(due)}" if due else ""
                    click.echo(f"  {content.lower()}{due_str}")
            
            if reminders:
                click.echo(f"\nREMINDERS ({len(reminders)}):")
                # Sort reminders alphabetically
                sorted_reminders = sorted(reminders, key=lambda x: x[1].lower())
                for task_id, content, category, focus, due, created in sorted_reminders:
                    click.echo(f"  {content.lower()}")
            
            context = get_context()
            click.echo(f"\nLIFE CONTEXT:\n{context}")
            click.echo(f"\n{CLAUDE_INSTRUCTIONS}")

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
            due_str = f" {format_due_date(due)}" if due else ""
            cat_label = f"[{category}]" if category == 'reminder' else ""
            click.echo(f"{task_id}: {focus_label}{content.lower()}{due_str} {cat_label}")

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