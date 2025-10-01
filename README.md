# Life

ADHD executive function rescue system. Because you can architect AI coordination protocols but can't remember to drink water.

## What This Is

CLI todo tracker that assumes you:
- Hyperfocus on fascinating problems
- Experience executive dysfunction on boring ones
- Build meta-tools to avoid actual tasks
- Respond to accountability, not encouragement
- Need harsh reminders about basic human maintenance

## Install

```bash
poetry install
```

## Core Concept

Three task zones:
- **FOCUS** (max 3): What you're pretending to do right now
- **BACKLOG**: Everything haunting you
- **REMINDERS**: Basic life maintenance you'll forget (water, sleep, sunlight, etc.)

Weekly momentum tracking to quantify your avoidance patterns.

## Usage

```bash
# Show dashboard with roast instructions for Claude
life

# Add task (atomic, minimal strings)
life task "thing"
life task "thing" --focus
life task "thing" --due 2025-12-01

# Add persistent reminder
life remind "hydrate"

# Complete task (fuzzy match)
life done "partial match"

# Toggle focus (fuzzy match)
life focus "partial"

# Update task
life update "partial" --content "new text"
life update "partial" --due 2025-12-01
life update "partial" --focus true

# Set life context for Claude
life context "Relationship: Crisis. Wedding: 52 days."

# Direct SQL when you need control
life sql "SELECT * FROM tasks WHERE focus = 1"

# List all tasks with IDs
life list
```

## For Claude

When you run `life`, you get:
- Current task state
- Weekly momentum (this week vs last week)
- Life context
- Roast instructions

Your job: Force conscious choice before work engagement. Refuse to be agreeable collaborator in avoidance. When Tyson rants about tasks, add them. When overwhelming, break into atomic steps. Make tradeoffs explicit.

## Schema

Single table, zero ceremony:

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    content TEXT,
    category TEXT,        -- 'task' or 'reminder'
    focus BOOLEAN,
    due DATE,
    created TIMESTAMP,
    completed TIMESTAMP
);
```

Context stored in `~/.life/context.md`.

## Philosophy

- Tasks are atomic and minimal. "Decide on X and order it" becomes "order X"
- Tyson sets focus and due dates, not Claude
- Break bundled tasks (X, Y, Z) into separate entries
- Reminders persist forever (they're maintenance, not completable)
- Harsh accountability > gentle encouragement
- Situational roasting based on momentum patterns

Reference grade code for a deeply unreference grade human.
