# Architecture

```
life/
  cli.py        - Typer router + command handlers (thin, calls domain modules)
  models.py     - dataclasses: Task, Habit, Tag, Weekly (no deps)
  db.py         - SQLite connection, migrations runner
  config.py     - DB path, profile config
  tasks.py      - task CRUD
  habits.py     - habit CRUD + check tracking
  tags.py       - tag add/remove
  dashboard.py  - pending items, today summary
  momentum.py   - weekly trend calculations
  health.py     - DB integrity checks
  migrations/   - numbered .sql migration files
  lib/          - shared infrastructure (no domain imports)
    errors.py   - echo(), exit_error()
    fuzzy.py    - find_task(), find_habit(), find_item(), find_task_any()
    render.py   - dashboard, habit matrix, momentum rendering
    format.py   - format_task(), format_habit(), format_status()
    ansi.py     - ANSI color constants
    backup.py   - DB backup
    clock.py    - today()
    dates.py    - named date tracking, due date parsing
    parsing.py  - CLI input parsing helpers
    converters.py - DB row → model converters
```

## Layer Boundaries

Higher imports lower. Never upward.

```
cli       → tasks, habits, tags, dashboard, momentum, lib, models
tasks     → db, models, lib/converters
habits    → db, models, lib/converters
tags      → db, models
dashboard → tasks, habits, models
momentum  → db, models
health    → db
lib       → models, db (converters only)
models    → (nothing)
db        → config
```

`lib/` must not import from domain modules (tasks, habits, tags, dashboard, momentum).

## Key Invariants

- `~/.life/life.db` is the single source of truth. Back up before risky ops.
- Every task must have a tag on entry.
- `lib/errors.py` owns all output: use `echo()` and `exit_error()`, never `typer.echo()` directly.

## What Needs Work

- `cli.py` still mixes routing and handler logic — extraction to `commands.py` would clean this.
