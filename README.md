# Life

ADHD executive function rescue system. Because you can architect AI coordination protocols but can't remember to drink water.

## What This Is

CLI todo tracker for humans who:
- Hyperfocus on fascinating problems
- Experience executive dysfunction on boring ones
- Build meta-tools to avoid actual tasks
- Respond to accountability, not encouragement
- Need harsh reminders about basic human maintenance

## The Pattern

Simple SQLite store + markdown context file. When Claude runs `life`, it sees:
- Current task state (focus, backlog, reminders)
- Weekly momentum tracking (quantified avoidance patterns)
- Life context from `~/.life/context.md`
- Embedded roast instructions

Claude's job: Force conscious choice before work engagement. Refuse agreeable collaboration in avoidance. When you rant about tasks, add them. When overwhelmed, break into atoms. Make tradeoffs explicit.

## Install

```bash
poetry install
life --help
```

## Usage

```bash
# Show dashboard + assessment
life

# Add task (atomic strings only)
life task "thing"
life task "thing" --focus
life task "thing" --due 2025-12-01

# Add habit (daily wellness/maintenance, checkable like reminders)
life habit "hydrate"

# Add chore (recurring maintenance tasks)
life chore "dishes"

# Check habit or chore (fuzzy match)
life check "partial match"

# Mark task done (fuzzy match)
life done "partial match"

# Toggle focus (max 3 active)
life focus "partial"

# Update task
life update "partial" --content "new text"
life update "partial" --due 2025-12-01
life update "partial" --focus true

# Set operational context (Claude reads this)
life context "Relationship: Crisis. Wedding: 52 days."

# Direct SQL for power users
life sql "SELECT * FROM tasks WHERE focus = 1"

# List all tasks with IDs
life list
```

## Architecture

Single table, zero ceremony:

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    content TEXT,
    category TEXT,        -- 'task', 'habit', or 'chore'
    focus BOOLEAN,
    due DATE,
    created TIMESTAMP,
    completed TIMESTAMP
);
```

Context stored in `~/.life/context.md` (markdown, human-readable, version-controllable).

## Categories

- **Task:** Project/event-specific work (wedding prep, mortgage, apartment projects). Has focus + due date. Completes when done.
- **Habit:** Daily wellness/maintenance (hydrate, exercise, sleep, meditation). Checkable each day like reminders were. Never "complete" (ongoing).
- **Chore:** Recurring maintenance (dishes, laundry, reset apartment). Checkable each day. Never "complete" (ongoing).

## Philosophy

- **Atoms, not bundles.** "Decide on X and order it" → "order X"
- **Human sets priorities.** You decide focus + due dates. Claude suggests atomization only.
- **Maintenance is visible.** Habits and chores tracked separately from project work (tasks).
- **Harsh > gentle.** Accountability pressure beats encouragement.
- **Momentum quantified.** Weekly delta exposes avoidance patterns objectively.
- **SQL as escape hatch.** Power users can query directly when CLI is constraining.
