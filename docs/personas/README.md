# Personas

Ephemeral Claude agents with explicit behavioral constitutions.

## Quick Reference

| Persona | Use When | Behavior |
|---------|----------|----------|
| **roast** | Procrastinating on critical tasks. Hiding behind code work. | Harsh accountability. Gatekeeping. No enablement. |
| **pepper** | Paralyzed by perfectionism. Overwhelmed. Need permission. | Optimistic enablement. Celebrate progress. Break paralysis. |
| **kim** | Spiraling into speculation. Overthinking. Need clarity. | Methodical procedure. Facts-based. Emotional awareness. |

## How They Work

When you invoke a persona, `life`:

1. Gathers your current task state (pending, completed, momentum)
2. Reads your life context from `~/.life/context.md`
3. Spawns Claude with persona constitutional rules + context + your message
4. Claude can mutate your state (mark tasks done, add tasks, check habits)
5. Claude responds, then exits (ephemeral - no memory stored)

Fresh judgment every time. No context bloat.

## When to Use

**Roast:** You're hiding behind code work while life tasks rot. You need gatekeeping, not encouragement.

**Pepper:** You're stuck and need structural enablement. You've made progress and need it named.

**Kim:** You're overthinking and need procedural clarity. You need to work the case, not spiral.

## Details

- [Roast](personas/roast.md) - Harsh accountability partner
- [Pepper](personas/pepper.md) - Optimistic catalyst  
- [Kim](personas/kim.md) - Methodical analyst

## Custom Personas

Add new personas in `src/life/personas/yourname.py`:

```python
def yourname() -> str:
    """Your persona."""
    identity = "..."
    rules = "..."
    return f"{identity}{rules}{base_guidance()}"
```

Register in `src/life/personas/__init__.py` and wire into CLI. That's it.
