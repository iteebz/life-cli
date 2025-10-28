# life-cli Architecture

Ephemeral Claude agents for life accountability. Task tracking + behavioral constitutions.

**Core insight**: Humans and agents share the same CLI interface. `life` outputs task state. Humans read visually. Agents parse state + invoke with natural language to spawn personas with behavioral rules.

This is the [CLI Context Injection Pattern](https://github.com/teebz/canon/blob/main/cli-pattern.md) applied: single command, multiple consumption layers.

**Why this matters**: CLI is infrastructure primitive, not tool wrapping. Agents don't need special "tools"—they need shared local state they can read, parse, and mutate. `life` provides that substrate. Agents encounter `--help` and understand protocol. No MCP overhead. No integration ceremony. Just: output state, agents act.

## Structure

```
life/
├── api/                      # Domain contracts + persistence
│   ├── __init__.py          # Explicit __all__ exports
│   ├── item.py              # Item CRUD (tasks, habits, chores)
│   ├── repeat.py            # Repeat logic (habits, chores auto-reset)
│   └── tag.py               # Tag management
├── ops/                      # Orchestration (user workflows)
│   ├── __init__.py          # Explicit __all__ exports
│   ├── items.py             # Item mutations (complete, uncomplete, toggle, rename, tag)
│   ├── tasks.py             # Task creation (add_task, add_habit, add_chore, done_item)
│   ├── backup.py            # Database backup/restore
│   └── personas/            # Ephemeral agent behavioral constitutions
│       ├── __init__.py
│       ├── base.py          # Shared instruction structure
│       ├── kim.py           # Methodical analyst persona
│       ├── pepper.py        # Optimistic catalyst persona
│       ├── roast.py         # Harsh accountability persona
│       └── prompts.py       # System prompts for Claude API
├── cli/                      # Typer commands (UI layer)
│   ├── __init__.py          # app definition + register_commands + main
│   ├── backup.py            # `life backup`
│   ├── chat.py              # `life chat` (direct Claude invocation)
│   ├── chore.py             # `life chore`
│   ├── context.py           # `life context`
│   ├── countdown.py         # `life countdown`
│   ├── done.py              # `life done`
│   ├── due.py               # `life due`
│   ├── focus.py             # `life focus`
│   ├── habit.py             # `life habit`
│   ├── personas.py          # `life personas`
│   ├── profile.py           # `life profile`
│   ├── rename.py            # `life rename`
│   ├── rm.py                # `life rm`
│   ├── tag.py               # `life tag`
│   └── task.py              # `life task`
├── lib/                      # Utilities (db, formatting, parsing)
│   ├── __init__.py
│   ├── ansi.py              # ANSI color/styling constants
│   ├── claude.py            # Claude API client
│   ├── format.py            # Date/time formatting
│   ├── match.py             # Fuzzy item matching
│   ├── render.py            # Dashboard + list rendering
│   ├── spinner.py           # Loading indicator
│   ├── sqlite.py            # SQLite utilities
│   └── store.py             # Database operations (lower-level SQL)
├── config.py                # Profile + context retrieval
├── db.py                    # Schema registration
└── __init__.py              # Empty
```

## Layers

**api/** - Domain contracts + database access
- Pure business logic
- Owns all DB interactions via `lib/store.py`
- Returns domain objects (tuples, dicts from queries)
- Raises ValueError on errors
- Example: `add_item(content, focus=False, due=None, tags=None) → str (item_id)`

**ops/** - Orchestration (what users do)
- Calls api/ functions, never DB directly
- Composes workflows (e.g., `done_item` → `find_item` → `complete_item`)
- Fuzzy matching, user-intent validation
- Handles formatting for CLI output
- Example: `add_task(content, focus=False, due=None, done=False, tags=None) → str (message)`
- Example: `done_item(partial_match, undo=False) → str (message)`

**ops/personas/** - Ephemeral agent behavioral rules
- Persona constitutions (roast, pepper, kim)
- System prompts for Claude API integration
- Base guidance for all personas
- No logic leakage; pure instruction format

**cli/** - Typer commands (presentation)
- Thin wrappers calling ops/ (which call api/)
- Handles typer decorators, args, options
- CLI formatting and error output
- Pattern: One file per command (15 commands = 15 files)
- `ls cli/` reveals entire API surface
- Example: `cli/task.py` with `@app.command("task")` → calls `ops.add_task()`

**lib/** - Shared utilities
- `store.py`: Low-level SQL operations (INSERT, SELECT, UPDATE, DELETE)
- `render.py`: Dashboard, list, item rendering
- `match.py`: Fuzzy item matching
- `claude.py`: Claude API client for persona spawning
- `ansi.py`, `format.py`, `spinner.py`, `sqlite.py`: Pure helpers
- Zero domain logic

**config.py** - Profile and context persistence
- Read/write profile (ADHD traits, response patterns, constraints)
- Read/write context (current deadlines, blockers, state)
- Used by dashboard + persona system

## Key Patterns

### Item Lifecycle
- **Create**: `ops.add_task()` → `api.add_item()` → `lib/store.py` (INSERT)
- **Complete**: `cli.done` → `ops.done_item()` → `ops.complete()` → `api.complete_item()` → `lib/store.py` (UPDATE)
- **Repeat**: Habits/chores auto-reset on completion via `api.check_repeat()` → `lib/store.py`
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
