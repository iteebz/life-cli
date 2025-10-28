# Personas

Ephemeral Claude agents with explicit behavioral constitutions.

| Persona | Use When |
|---------|----------|
| **roast** | Procrastinating on critical tasks. Hiding behind code work. |
| **pepper** | Paralyzed by perfectionism. Overwhelmed. Need permission. |
| **kim** | Spiraling into speculation. Overthinking. Need clarity. |

- [Roast](roast.md) - Harsh accountability partner
- [Pepper](pepper.md) - Optimistic catalyst  
- [Kim](kim.md) - Methodical analyst

## Custom Personas

Add new personas in `life/ops/personas/yourname.py`:

```python
def yourname() -> str:
    identity = "..."
    rules = "..."
    return f"{identity}{rules}{base_guidance()}"
```

Register in `life/ops/personas/__init__.py` and wire into CLI.
