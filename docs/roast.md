# The Ephemeral Agent Pattern

How Life spawns Claude instances with task context and behavioral constitutions.

## The Core Idea

Instead of building persistent "AI assistants" with memory systems, Life spawns ephemeral Claude instances that:
1. Read your current task state
2. Get explicit behavioral rules (constitution)
3. Respond to your message
4. Exit

Fresh judgment every time. No context bloat. Simple, honest, effective.

## Why Ephemeral?

**Traditional AI assistants:**
- Store conversation history
- Build up context over time
- Develop "personalities" through accumulated interactions
- Become harder to debug as memory grows
- Expensive to maintain

**Ephemeral agents:**
- No memory between interactions
- Fresh judgment every spawn
- Explicit rules embedded in prompt
- Completely reproducible
- Trivially cheap
- Constitutional, not emergent

## How It Works

### 1. Message Detection

```python
life "your message here"
```

CLI checks: is this a known command or a natural language message?

If message (not command), proceed to agent spawn.

### 2. Context Gathering

Life pulls:
- All pending tasks (with focus + due dates)
- Completed tasks today
- Weekly momentum (completed vs pending)
- Life context from `~/.life/context.md`
- Task history (patterns over time)

This becomes the `<CONTEXT>` in the spawned prompt.

### 3. Constitution Loading

Based on the persona specified (roast/pepper/kim/custom), Life loads the constitutional rules:

```python
constitution = get_persona("roast")
```

This includes:
- Identity statement
- Critical principles
- Job description
- Pattern recognition rules
- CLI operations guide

### 4. Prompt Assembly

```
[CONSTITUTION]

---
User says: {message}

Run `life` to see their task state. Respond as {persona}: 
assess patterns, guide appropriately, use CLI to modify state as needed.
```

Claude gets:
- Explicit behavioral rules
- Your full task context
- Your message
- Access to `life` CLI

### 5. Claude Responds

Claude can:
- Analyze your task state
- Call out patterns
- Suggest atomization
- Mark tasks done via CLI
- Add new tasks
- Check off habits/chores
- Respond in chat

### 6. Session Ends

Claude finishes responding. The ephemeral instance exits. No memory stored.

Next time you invoke a persona, it starts fresh.

## Why This Works

### 1. Ephemeral = Fresh Judgment
- No accumulated context bias
- No "established narrative" about your patterns
- Each assessment is independent
- Simpler, clearer reasoning

### 2. Constitutional = Predictable
- Rules are explicit in the prompt
- You can read, understand, modify them
- Behavior is reproducible
- Not a black box

### 3. CLI-Native = Natural
- Claude uses the exact same interface you use
- State mutations are real (tasks actually get marked done)
- No special APIs or hidden plumbing
- What you see is what Claude sees

### 4. Task Context = Reality-Based
- Claude judges based on actual state, not assumptions
- Can see pending work, momentum, priorities
- Decision-making is informed by facts
- No guessing about your situation

## The Constitutional Structure

Each persona is assembled from modular components:

```python
identity = "[PERSONA IDENTITY]..."      # Who are you?
critical = "[CRITICAL PRINCIPLES]..."   # What won't you do?
job = "[YOUR JOB]..."                   # What should you do?
patterns = "[PATTERNS TO WATCH]..."     # What do you look for?
cli_ops = cli_operations()              # How do you use the CLI?
guidance = base_guidance()              # General guidance about state

return f"{identity}{critical}{job}{patterns}{cli_ops}{guidance}"
```

### The Base Guidance (All Personas Get This)

Explains:
- How to read task state from `life` command
- How to mutate state (mark done, add tasks)
- How to interpret momentum
- What context.md means
- When to use CLI vs when to just advise

Ensures consistency across all personas.

### Persona-Specific Rules

Each persona then adds its own critical principles:

**Roast:**
```
- Enabling code work while life neglected = harm
- Refusal = actual care
- Call out avoidance by name
```

**Pepper:**
```
- Smart people paralyze with perfectionism
- Your job: simplify path forward
- Celebrate what's working
```

**Kim:**
```
- Emotional awareness fine, caretaking not
- Focus on facts and procedure
- Work the case, don't fix them
```

## Examples

### Example 1: Roast Gatekeeping

```bash
$ life "can you help me optimize my database queries?"

[life gathers: 6 pending critical tasks, wedding in 60 days, vows not written]

roast constitution: "Enabling code work while life neglected = harm"

roast: No. You have 6 pending life tasks. One of them is "write vows" 
and your wedding is 60 days away. I'm not helping with code.

Fix the life tasks first. Then come back.
```

### Example 2: Pepper Enablement

```bash
$ life pepper "i finished the presentation but it's not perfect"

[life gathers: presentation task marked done, momentum recovering from burnout, 
perfectionism pattern detected]

pepper constitution: "Smart people paralyze with perfectionism. Simplify path forward."

pepper: Stop. It's done. Perfect is the enemy of shipped.

You're recovering from burnout - protecting that momentum IS the win here. 
Ship it. Move on. I'm adding "send presentation to stakeholders" so you 
have closure.

[runs: life task "send presentation to stakeholders"]
```

### Example 3: Kim Procedure

```bash
$ life kim "i'm not sure if this project is worth continuing"

[life gathers: project in progress, 3 focus items, momentum stable]

kim constitution: "Focus on facts, procedure, and evidence. Work the case."

kim: Detective. Let's establish decision criteria.

What matters to you: Revenue trajectory? Personal fulfillment? Market timing? 
Skill growth? Get those on the table first.

Currently: You have 3 active items. Finish those, then reassess the project 
with data instead of uncertainty.
```

## Implementation Details

### Constitution as String Concatenation

```python
def roast() -> str:
    identity = "..."
    critical = "..."
    job = "..."
    patterns = "..."
    return f"{identity}{critical}{job}{patterns}{cli_operations()}{base_guidance()}"
```

No classes, no state, no complexity. Just strings. The entire persona is one function that returns text.

This is intentional: constitutions should be readable, editable, transparent.

### CLI Access is Real

When Claude runs commands like:
```bash
life done "write vows"
life task "send presentation"
life check "dishes"
```

These actually modify your task database. State mutation is real-time.

This makes accountability possible: if Roast says something should be a task, it becomes a task immediately.

### Task Context is Complete

The CLI output that Claude sees includes:

```
PENDING TASKS (7):
  [FOCUS] 1: write vows (due 2025-11-15)
  2: buy wedding ring
  3: practice first dance
  [FOCUS] 4: finish proposal draft
  ...

MOMENTUM:
  This week: 12 completed, 14 pending
  Last week: 8 completed, 18 pending
  Trend: +33% completion (recovering)

LIFE CONTEXT:
  Wedding: Nov 15 (52 days)
  Vows: not written
  Ring: need to buy
  Project: AI governance protocols
  Health: sleep erratic, exercise none this week

[CLAUDE: Assess patterns, react appropriately, use CLI to modify state]
```

Claude sees everything you see. Decisions are based on actual state, not imagination.

## Philosophy

### Tools are Instruction Delivery

The CLI output tells Claude exactly how to behave.

This is the same philosophy as ShitLint: the tool interface itself is an instruction mechanism.

You don't build "AI that reads your intentions." You build tools that tell Claude explicitly what to do.

### Constitution > Personality

"Personalities" are emergent and unpredictable. Constitutions are explicit.

Each persona has rules you can read, understand, and modify. Not a vibe - actual governance.

### Humans Decide, Claude Executes

You set:
- Priorities (focus + due dates)
- Context (life situation in context.md)
- Categories (task/habit/chore)
- Constitutional rules (which persona to use)

Claude:
- Recognizes patterns
- Suggests atomization
- Enforces accountability
- Modifies state
- Judges

Clear division of labor.

## Extending the Pattern

### Adding a New Persona

1. Create `src/life/personas/yourname.py`
2. Define function that returns constitution string
3. Register in `__init__.py`
4. Wire into CLI (3 places)
5. Done

No complex framework. No special plumbing. Just a function that returns text.

### Customizing Personas

Edit the constitution strings directly:

```python
critical = (
    "CRITICAL PRINCIPLES:\n"
    "- Your custom rule here\n"
    "- Another rule\n\n"
)
```

Change what the persona does by changing the text.

### Multi-Persona Sessions

You can invoke different personas for different perspectives:

```bash
life roast "should i keep working?"
# Roast: no, you have pending life tasks

life pepper "but i'm making good progress"
# Pepper: exactly, protect that momentum

life kim "is this a productivity question or a life priority question?"
# Kim: let's define what matters to you first
```

Each persona gives independent judgment. You choose which to listen to.

## The Meta Point

This pattern generalizes beyond Life.

Any place where you need Claude to:
- Have persistent context
- Follow explicit behavioral rules
- Actually modify your system state
- Provide fresh judgment without memory bloat

...you can use the ephemeral agent pattern.

Task tracking. Research coordination. Code review. Habit enforcement. Decision-making frameworks.

Same architecture: CLI + task context + constitutional rules + state mutation.

The tool is the instruction mechanism. Claude executes. State changes happen.

That's it.
