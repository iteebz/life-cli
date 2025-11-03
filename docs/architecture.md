# life-cli Architecture

Ephemeral Claude agents for life accountability. Task tracking + behavioral constitutions.

**Core insight**: Humans and agents share the same CLI interface. `life` outputs task state. Humans read visually. Agents parse state + invoke with natural language to spawn personas with behavioral rules.

This is the [CLI Context Injection Pattern](https://github.com/teebz/canon/blob/main/cli-pattern.md) applied: single command, multiple consumption layers.

**Why this matters**: CLI is infrastructure primitive, not tool wrapping. Agents don't need special "tools"—they need shared local state they can read, parse, and mutate. `life` provides that substrate. Agents encounter `--help` and understand protocol. No MCP overhead. No integration ceremony. Just: output state, agents act.

## Structure

```
life/
├── api/                      # Domain logic + data access
│   ├── __init__.py
│   ├── dashboard.py         # Dashboard data aggregation
│   ├── dates.py             # Date CRUD (pure, no I/O)
│   ├── habits.py            # Habit CRUD + checks
│   ├── momentum.py          # Weekly momentum calculations
│   ├── personas.py          # Persona selection + prompt building
│   ├── tags.py              # Tag operations
│   ├── tasks.py             # Task CRUD
│   └── utils.py             # Internal utilities
├── cli.py                    # Typer commands (presentation layer)
│   ├── callbacks            # Default dashboard view
│   ├── task                 # `life task`
│   ├── habit                # `life habit`
│   ├── done                 # `life done`
│   ├── rm                   # `life rm`
│   ├── focus                # `life focus`
│   ├── due                  # `life due`
│   ├── rename               # `life rename`
│   ├── tag                  # `life tag`
│   ├── habits               # `life habits`
│   ├── profile              # `life profile`
│   ├── context              # `life context`
│   ├── dates                # `life dates` (add, remove, list)
│   ├── backup               # `life backup`
│   ├── personas             # `life personas`
│   ├── chat                 # `life chat`
│   └── list                 # `life list`
├── lib/                      # Utilities (db, format, parse, render)
│   ├── __init__.py
│   ├── ansi.py              # ANSI color/styling
│   ├── backup.py            # Database backup/restore
│   ├── claude.py            # Claude API client
│   ├── clock.py             # Date/time utilities
│   ├── converters.py        # Row-to-object conversions
│   ├── dates.py             # Date parsing
│   ├── errors.py            # Custom exceptions
│   ├── format.py            # Task/habit formatting for CLI
│   ├── fuzzy.py             # Fuzzy item matching
│   ├── parsing.py           # Argument parsing
│   ├── render.py            # Dashboard + list rendering
│   └── spinner.py           # Loading indicator
├── personas/                 # Persona behavioral constitutions
│   ├── __init__.py
│   ├── base.py              # Shared instruction structure
│   ├── kim.py               # Methodical analyst persona
│   ├── pepper.py            # Optimistic catalyst persona
│   └── roast.py             # Harsh accountability persona
├── migrations/              # Database schema migrations
│   └── 001_foundation.sql
├── config.py                # Config singleton (profile, context, dates)
├── db.py                    # Schema registration + connection pool
└── __init__.py              # Empty
```

## Layers

**api/** - Domain logic + data access
- Pure business logic, no I/O or presentation concerns
- Functions return data (dicts, lists, objects), not formatted strings
- Raises ValueError on errors
- Owns all DB interactions
- Examples:
  - `add_task(content, focus=False, due=None, tags=None) → str (task_id)`
  - `list_dates() → list[dict]`
  - `get_persona_instructions(name: str) → str`

**cli.py** - Typer command handlers (presentation layer)
- One function per command (task, habit, done, etc.)
- Calls api/ functions to get data
- Handles all typer decorators, argument parsing, options
- Responsible for formatting output and error messages
- Catches api/ exceptions and translates to user-friendly output
- Example: `dates()` command calls `list_dates()`, formats output, echoes

**personas/** - Ephemeral agent behavioral constitutions
- Pure instruction text for Claude API
- Roast, pepper, kim behavioral rules (no logic)
- Built by `api/personas.py` via `_build_persona_prompt()`

**lib/** - Shared utilities
- `render.py`: Dashboard, list rendering
- `format.py`: Task/habit CLI formatting (symbols, dates, tags)
- `fuzzy.py`: Fuzzy item matching
- `claude.py`: Claude API client
- `clock.py`, `ansi.py`, `converters.py`, `parsing.py`: Pure helpers
- Zero domain logic

**config.py** - Config singleton
- Single-instance Config class (load once, cache in memory)
- Provides `.get(key)` and `.set(key, value)` methods
- Module-level API for backwards compatibility
- Used by dashboard, personas, and CLI for profile/context/dates

## Key Patterns

### Item Lifecycle
- **Create**: `ops.add_task()` → `api.add_item()` → `lib/store.py` (INSERT)
- **Complete**: `cli.done` → `ops.done_item()` → `ops.complete()` → `api.complete_item()` → `lib/store.py` (UPDATE)
- **Repeat**: Habits auto-reset on completion via `api.add_check()` → `lib/store.py`
- **Matching**: Fuzzy matching via `lib/match.find_item()` for user input

### Persona System (Agent Behavior Constitution)
1. User invokes `life "message"` (natural language, not a command)
2. `cli/__init__.py:main()` calls `ops.personas.maybe_spawn_persona()`
3. Persona system:
   - Gathers task state from dashboard (same output humans see)
   - Reads profile + context (user identity + current situation)
   - Loads persona constitutional rules (roast/pepper/kim behavioral instructions)
   - Constructs Claude API call with all three inputs
4. Claude responds with accountability/guidance (can mutate state via CLI)
5. Ephemeral agent exits (no memory stored, fresh judgment next time)

Personas are the mechanism for agent behavior constitution. No special output tags needed—behavioral rules injected at invocation time.

### Formatting Layer
- Dashboard: `lib/render.render_dashboard()` (pending tasks, momentum, context, completion)
- Lists: `lib/render.render_item_list()` (for `life list`)
- CLI output: Ops layer returns formatted strings (messages with ✓, [FOCUS], #tags, etc.)

## Testing

- **Unit tests** in `tests/unit/` mirror codebase structure
  - `tests/unit/api/` - Pure domain logic
  - `tests/unit/ops/` - Orchestration workflows
  - `tests/unit/lib/` - Utility functions
- **Integration tests** in `tests/integration/`
  - CLI command execution
  - Full workflows (create → complete → verify)

## Audit Principle

- **api/** is testable in isolation (mock db)
- **ops/** is testable without typer or CLI
- **cli/** stays thin (routing, not logic)
- **lib/** contains only pure utilities or helpers
- No ceremony, no forwarding without logic
