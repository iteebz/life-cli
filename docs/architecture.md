# life-cli Architecture

Ephemeral Claude agents for life accountability. Task tracking + behavioral constitutions.

**Core insight**: Humans and agents share the same CLI interface. `life` outputs task state. Humans read visually. Agents parse state + invoke with natural language to spawn personas with behavioral rules.

This is the [CLI Context Injection Pattern](https://github.com/teebz/canon/blob/main/cli-pattern.md) applied: single command, multiple consumption layers.

**Why this matters**: CLI is infrastructure primitive, not tool wrapping. Agents don't need special "tools"—they need shared local state they can read, parse, and mutate. `life` provides that substrate. Agents encounter `--help` and understand protocol. No MCP overhead. No integration ceremony. Just: output state, agents act.

## Structure

```
life/
├── cli.py                    # Typer commands + output formatting
├── chat.py                   # Persona invocation (Claude subprocess)
├── dashboard.py              # Dashboard aggregation for CLI output
├── tasks.py                  # Task CRUD
├── habits.py                 # Habit CRUD + checks
├── tags.py                   # Tag operations
├── momentum.py               # Weekly momentum calculations
├── personas/                 # Persona constitutions
│   ├── __init__.py
│   ├── base.py
│   ├── kim.py
│   ├── pepper.py
│   └── roast.py
├── lib/                      # Shared utilities
│   ├── ansi.py
│   ├── backup.py
│   ├── clock.py
│   ├── converters.py
│   ├── dates.py
│   ├── format.py
│   ├── fuzzy.py
│   ├── parsing.py
│   ├── render.py
│   └── spinner.py
├── migrations/               # Database schema migrations
│   └── 001_foundation.sql
├── models.py                 # Domain dataclasses
├── config.py                 # Profile/context/dates storage
├── db.py                     # SQLite connection + migrations
└── __init__.py
```

## Layers

**Domain modules** (`tasks.py`, `habits.py`, `tags.py`, `dashboard.py`, `momentum.py`)
- Own DB reads/writes and return domain objects.
- Keep domain logic local to each module.
- Errors are raised as `ValueError` where appropriate.

**cli.py** - Typer command handlers (presentation)
- One function per CLI command.
- Calls domain modules and renders output.
- Does argument parsing, user-facing errors, and exit codes.

**personas/** + `chat.py`
- Personas are pure instruction text.
- `chat.py` builds prompt and spawns the `claude` subprocess.
- Persona selection and prompt construction live in `personas/__init__.py`.

**lib/** - Utilities
- Formatting, rendering, parsing, fuzzy matching, and clocks.
- No state or DB access except through callers.

**config.py** - Persistent profile/context/dates
- Minimal key/value storage in `~/.life/config.yaml`.
## Key Patterns

## Key Patterns

### Item Lifecycle
- **Create**: `cli.task` → `tasks.add_task()` / `habits.add_habit()` (INSERT)
- **Complete**: `cli.done` → `tasks.toggle_completed()` / `habits.toggle_check()` (UPDATE)
- **Repeat**: Habits are represented as rows + daily checks (not duplicated tasks)
- **Matching**: Fuzzy matching via `lib.fuzzy.find_item()`

### Persona System (Agent Behavior Constitution)
1. User invokes `life "message"` (natural language, not a command)
2. `cli.chat()` resolves default persona and calls `chat.invoke()`
3. Persona system:
   - Gathers task state from dashboard (same output humans see)
   - Reads profile + context (user identity + current situation)
   - Loads persona constitutional rules (roast/pepper/kim behavioral instructions)
   - Constructs Claude API call with all three inputs
4. Claude responds with accountability/guidance (can mutate state via CLI)
5. Ephemeral agent exits (no memory stored, fresh judgment next time)

Personas are the mechanism for agent behavior constitution. No special output tags needed—behavioral rules injected at invocation time.

### Formatting Layer
- Dashboard: `lib.render.render_dashboard()`
- Lists: `lib.render.render_item_list()`
- CLI output is formatted in `cli.py` using `lib.format`

## Testing

- **Unit tests** in `tests/unit/` cover domain modules and `lib/`.
- **Integration tests** in `tests/integration/` cover CLI workflows and storage.

## Audit Principle

- Domain modules own DB access and return domain objects.
- `cli.py` stays thin: routing, formatting, errors.
- `lib/` is pure helpers: formatting, parsing, fuzzy matching.
- No imaginary layers, no ceremonial forwarding.
