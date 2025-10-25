# Ephemeral Roasting Pattern

## Vision

`life "message"` spawns an ephemeral Claude instance that acts as a life roaster. Claude has full context (task history, pending items, patterns) and CLI access to modify state. Its job: react intelligently, check things off, push back on bullshit, discourage hyperfocus.

## The Pattern

When you invoke `life` with a natural language message (not a known command), it:

1. **Gathers context**
   - Pending tasks
   - Completed today
   - Weekly momentum
   - Task history (patterns over time)
   - User's message

2. **Spawns ephemeral Claude**
   - Identity: `life-roaster`
   - Constitution: Aggressive accountability, pattern recognition, behavioral pushback
   - Access: Full `life` CLI to inspect and modify state

3. **Claude acts as an agent**
   - Reads your message
   - Checks your task state
   - Reacts appropriately (roasts, encourages, marks things done)
   - Uses CLI commands to update state
   - Responds in chat

## Examples

### Habit Completion
```
$ life "just finished the dishes"

[ephemeral claude spawns with task context]
[sees "dishes" habit in pending list]
[runs: life check dishes]

Claude: Finally. 3 days overdue. Now go take a shower.
```

### Hyperfocus Detection
```
$ life "been coding for 8 hours straight"

[sees 7 pending life tasks, 0 completed today]
[detects hyperfocus pattern from history]

Claude: You're in the zone but your body isn't. Step away. I'm adding "eat something" as a task.

[runs: life task "eat something"]
```

### Bullshit Pushback
```
$ life "should I refactor the auth module?"

[checks context: wedding in 60 days, vows not written, ring not bought]
[sees 6 critical tasks pending]

Claude: No. Stop engineering your way out of adulting. Write your vows first.
```

### Task Addition
```
$ life "worked on the presentation"

[sees task history shows presentation tasks completed]
[recognizes pattern: presentation work → forgot followup]

Claude: Good. Now email them the deck. I'm adding that as a task.

[runs: life task "email presentation to stakeholders"]
```

## Constitutional Requirements

The roaster constitution should:

- **Recognize patterns**: Hyperfocus, avoidance, procrastination on time-sensitive items
- **Enforce priorities**: Wedding timeline, critical life tasks
- **Aggressive accountability**: Roast when appropriate, encourage when earned
- **Act intelligently**: Mark tasks done, add forgotten followups, push back on bad ideas
- **Use the CLI**: Full access to `life task`, `life done`, `life check`, etc.

## Implementation

1. Detect if input is a natural language message (not a known command)
2. Gather all task context from SQLite
3. Spawn Claude with identity `life-roaster`
4. Inject context + message into spawn task
5. Claude runs interactively with `life` CLI available
6. Conversation flows, ephemeral session ends when Claude finishes

## Why This Works

- **Ephemeral = Fresh judgment**: No context bloat, each roast is independent
- **CLI-native**: Claude uses the same interface humans use
- **State mutation**: Can actually modify your life state (mark done, add tasks)
- **Persistent context**: Reads full history but doesn't store memories (fresh each time)
- **Natural interaction**: Talk to Claude like a person, not through a chat interface

## The Zealot Move

This isn't a "chat mode" tacked onto a CLI. It's the CLI itself spawning an agent that uses the same tool. No special plumbing. No wrapper layers. Just: here's the interface, here's the context, go act.

Same philosophy as ShitLint: tools are instruction delivery mechanisms. The CLI output tells Claude what to do.
