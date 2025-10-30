# life-cli

Life accountability CLI. Task tracking + ephemeral Claude personas that hold you accountable.

When you talk to `life`, you're spawning a Claude agent with your full task context and explicit behavioral rules.

Perfect for:
- Accountability that matches your ADHD, not against it
- Responding to directness, not encouragement
- Task tracking that actually works

## Quick Start

```bash
poetry install
life --help
```

## Setup

Before spawning personas, configure profile and context:

```bash
# Set identity + work patterns
life profile "Senior IC. ADHD. Respond to directness, not encouragement. No meetings before noon. Coding energizes me. Writing drains me."

# Set current reality (update when circumstances change)
life context "Sprint deadline Friday. Auth module blocked. Running on 6h sleep. Relationship strain."

# Set default persona to avoid typing it each time
life personas roast -s
```

See [docs/architecture.md](docs/architecture.md) for system design.

## Usage

**Same interface for humans and agents.** Both run `life` to read task state. Agents add natural language to spawn personas.

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

# Mark done (fuzzy match)
life done "partial match"

# Check habit (fuzzy match)
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

Each persona has distinct behavioral constitution. See [Personas](#personas) below.

## Personas

Ephemeral Claude agents with different behavioral constitutions. See [docs/personas](docs/personas/) for details.

| Persona | Use When | Style |
|---------|----------|-------|
| **roast** | You need gatekeeping. Procrastinating on critical tasks. Hiding behind code work. | Harsh accountability. No enablement. |
| **pepper** | You're paralyzed by perfectionism. Overwhelmed. Need permission to move forward. | Optimistic catalyst. Celebrate progress. |
| **kim** | Spiraling into speculation. Need procedural clarity. Overthinking. | Methodical. Facts-based. Stable. |

## Categories

- **Task:** Project work with due dates. Mark done when complete.
- **Habit:** Daily wellness (hydrate, exercise, sleep). Checkable daily. Never "complete."

