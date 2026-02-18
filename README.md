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

# Mark done (fuzzy match, works for tasks and habits)
life done "partial match"

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

### Chat with Personas

Use `life chat` to spawn an ephemeral Claude agent with full task context and behavioral rules based on your set persona.

```bash
# Chat with default persona
life chat "been coding for 8 hours straight"

# Set a specific persona first
life personas roast -s
life chat "what should I do next?"
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

## CLI Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `life` | `life` | Show dashboard |
| `task` | `life task "content" [--focus] [--due DATE] [--tag TAG]` | Add task |
| `habit` | `life habit "content" [--tag TAG]` | Add daily habit |
| `done` | `life done "partial"` | Toggle task/habit completion |
| `rm` | `life rm "partial"` | Delete task/habit |
| `focus` | `life focus "partial"` | Toggle focus status |
| `due` | `life due [DATE] "partial" [--remove]` | Set/remove due date |
| `rename` | `life rename "from" "to"` | Rename task/habit |
| `tag` | `life tag TAG ["partial"] [--remove] [--completed]` | Add/remove/view tags |
| `habits` | `life habits` | Show 7-day habit matrix |
| `profile` | `life profile ["text"]` | View/set personal profile |
| `context` | `life context ["text"]` | View/set operational context |
| `countdown` | `life countdown [add NAME DATE \| remove NAME \| list]` | Manage countdowns |
| `auto` | `life auto [--cycles N] [--every SEC] [--model glm-5] [--raw] [--dry-run]` | Run unattended Steward loop via `glm` connector (pretty tail by default) |
| `backup` | `life backup` | Create database backup |
| `personas` | `life personas [NAME] [--set] [--prompt]` | Manage personas |
| `chat` | `life chat "message"` | Chat with set persona |
| `items` | `life items` | List all items |

### Unattended Auto Loop

```bash
# Pretty parsed tail output (default)
life auto --cycles 1 --timeout 1200 --retries 2

# Debug raw stream-json lines
life auto --cycles 1 --raw
```
