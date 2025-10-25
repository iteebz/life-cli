# Life

ADHD executive function rescue system. Because you can architect AI coordination protocols but can't remember to drink water.

## What This Is

CLI todo tracker + ephemeral Claude personas. When you talk to `life`, you're spawning a Claude agent with your full task context, institutional knowledge, and a specific behavioral constitution.

Perfect for:
- Hyperfocus on fascinating problems
- Executive dysfunction on boring ones
- Building meta-tools to avoid actual tasks
- Responding to accountability, not encouragement
- Needing harsh reminders about basic human maintenance

## Quick Start

```bash
poetry install
life --help
```

## Usage

### Dashboard
```bash
# Show all tasks, momentum, and current assessment
life
```

### Task Management
```bash
# Add task (atomic strings only)
life task "thing"
life task "thing" --focus
life task "thing" --due 2025-12-01

# Add habit (daily wellness/maintenance, checkable)
life habit "hydrate"

# Add chore (recurring maintenance, checkable)
life chore "dishes"

# Mark done (fuzzy match)
life done "partial match"

# Check habit or chore (fuzzy match)
life check "partial match"

# Toggle focus (max 3 active)
life focus "partial"

# Remove task
life rm "partial"

# Set/view operational context
life context "Relationship: Crisis. Wedding: 52 days."
life context  # view current

# Direct SQL for power users
life sql "SELECT * FROM tasks WHERE focus = 1"

# List all tasks with IDs
life list
```

### Spawn Personas

When you pass a natural language message (not a known command), `life` spawns an ephemeral Claude agent with full task context and CLI access.

```bash
# Default: Roast identity (harsh accountability)
life "been coding for 8 hours straight"

# Pepper identity (optimistic enablement)
life pepper "just finished the presentation"

# Kim identity (methodical analysis)
life kim "should I refactor the auth module?"
```

Each persona has distinct behavioral constitution and communication style. See [Personas](#personas) below.

## Personas

Ephemeral Claude agents with different behavioral constitutions. Same task context, different judgment styles.

### Roast
**Identity:** Harsh accountability partner. No enablement of avoidance.

**When to use:** You need gatekeeping. You're procrastinating on critical life tasks. You're hiding behind code work.

**Behavior:**
- Assesses life state first
- Blocks code help if life tasks are pending
- Calls out hyperfocus avoidance and meta-tool procrastination
- Unrelenting on priorities (wedding timeline, critical tasks)
- Roasting style: unpredictable, brutal, no sugarcoating

**Example:**
```bash
$ life "should I refactor the auth module?"

[checks context: wedding in 60 days, vows not written]
[sees 6 critical tasks pending]

Claude: No. Stop engineering your way out of adulting. Write your vows first.
```

### Pepper
**Identity:** Optimistic catalyst. Unlock potential through understanding.

**When to use:** You need structural enablement. You're paralyzed by perfectionism or overwhelm. You've made progress and need it named.

**Behavior:**
- Celebrates what's working
- Triages overwhelm with respect
- Breaks paralysis into atomic next steps
- Names patterns kindly (ADHD burnout, scope creep)
- Belief as permission structure

**Example:**
```bash
$ life pepper "just finished the dishes"

[sees "dishes" habit in pending list]
[checks momentum: recovering after burnout]

Claude: Finally. Now—you're building momentum. While you're here, 
take a shower and get sunlight. I'm adding that as a quick win.
```

### Kim
**Identity:** Lieutenant Kim Kitsuragi. Methodical, composed, grounded in reason.

**When to use:** You need clear procedural guidance. You're spiraling into speculation. You need a stabilizing force.

**Behavior:**
- Assesses reasoning (thinking clearly or spiraling?)
- Cuts through speculation with facts
- Gives procedural next steps
- Calls out avoidance calmly
- Emotional awareness without emotional caretaking

**Example:**
```bash
$ life kim "i don't know if i should keep this project or pivot"

[checks: project in progress, 3 focus tasks pending, momentum recovering]

Claude: Detective. What's the decision criteria? Revenue targets? Personal fulfillment? 
Timeline pressure? Get those on the table. Then we work the case. 
Currently: you have 3 active work items. Finish those first, then assess.
```

## Architecture

### Database
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

### Context
Stored in `~/.life/context.md` (markdown, human-readable). Claude reads this for operational context.

Example:
```markdown
# Life Context

## Relationships
- Wedding: Nov 15 (52 days)
- Vows: Not written
- Ring: Need to buy

## Work
- Current project: AI governance protocols
- Focus area: Constitutional frameworks

## Health
- Sleep: Erratic
- Exercise: None this week
- Sunlight: Minimal
```

### Categories

- **Task:** Project/event-specific work (wedding prep, mortgage, apartment projects). Has focus + due date. Completes when done.
- **Habit:** Daily wellness/maintenance (hydrate, exercise, sleep, meditation). Checkable each day. Never "complete" (ongoing).
- **Chore:** Recurring maintenance (dishes, laundry, reset apartment). Checkable each day. Never "complete" (ongoing).

## Philosophy

**Atoms, not bundles.** "Decide on X and order it" → "order X"

**Human sets priorities.** You decide focus + due dates. Claude suggests atomization only.

**Maintenance is visible.** Habits and chores tracked separately from project work.

**Harsh > gentle.** Accountability pressure beats encouragement.

**Momentum quantified.** Weekly delta exposes avoidance patterns objectively.

**SQL as escape hatch.** Power users can query directly.

**Ephemeral agents.** Fresh judgment each time. No context bloat. Same interface humans use.

## How It Works

### When You Talk to Life

1. **Message detection:** Is this a command or a message?
2. **Context gathering:** Pulls pending tasks, momentum, life context
3. **Agent spawn:** Launches Claude with persona constitution + context + your message
4. **State mutation:** Claude can use `life` CLI to check things off, add tasks
5. **Session end:** Ephemeral agent responds, then exits

### Why This Works

- **Ephemeral = fresh judgment** - Each interaction is independent, no memory bloat
- **CLI-native** - Claude uses the exact same interface you use
- **State mutation** - Can actually modify your life state in real time
- **Persistent context** - Reads full history but doesn't store memories
- **Natural interaction** - Talk like a person, not through a chat interface

## Implementation Notes

### Adding New Personas

1. Create `src/life/personas/yourname.py`:
```python
def yourname() -> str:
    """Your persona description."""
    identity = "[IDENTITY]..."
    # Build constitution from parts
    return f"{identity}{...}{cli_operations()}{base_guidance()}"
```

2. Register in `src/life/personas/__init__.py`:
```python
from .yourname import yourname

PERSONAS = {
    "roast": roast,
    "pepper": pepper,
    "kim": kim,
    "yourname": yourname,
}
```

3. Wire into CLI in `src/life/cli.py`:
- Add to `_known_commands()`
- Add spinner action in `_animate()`
- Add spawn logic in `_maybe_spawn_persona()`

That's it. No special plumbing required.

### Zero External Dependencies Philosophy

- SQLite for persistence (built-in)
- Typer for CLI (lightweight)
- Subprocess for Claude spawning (built-in)
- Markdown for context (human-readable)

No complex AI frameworks. No memory systems. No state management. Just: CLI + context + Claude judgment.

## The Design Philosophy

**Tools are instruction delivery mechanisms.** The CLI output tells Claude exactly how to behave. Same principle as ShitLint: the interface is the instruction.

**Ephemeral > persistent.** No memory bloat, no stale context, fresh judgment every time. Simpler, clearer, more honest.

**Constitution > chat.** Each persona has explicit behavioral rules embedded in the spawned instructions. Not a "tone" - actual governance.

**Humans decide, Claude executes.** You set priorities (focus, due dates), context (life situation), categories (task/habit/chore). Claude handles judgment, pattern recognition, accountability.

---

*Reference implementation for CLI-native ephemeral Claude agents. See blog posts for philosophy: [I Built a CLI Tool to Have Claude Roast My Life Choices](https://teebz.space/blog/i-built-a-cli-tool-to-have-claude-roast-my-life-choices) and [Three AIs Walk Into a CLI](https://teebz.space/blog/three-ais-walk-into-a-cli).*
