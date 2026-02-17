Read ARCH.md for structure and layer boundaries.

The CLI entry point is `life/cli.py`. Domain logic lives in `life/tasks.py`, `life/habits.py` etc. Shared infrastructure is in `life/lib/`. Output via `echo()`, errors via `exit_error()` — both in `life/lib/errors.py`.

Resolve user refs (fuzzy string, UUID prefix) at the CLI boundary using `lib/resolve.py`. Commands call `resolve_task(ref)` / `resolve_item(ref)` — domain functions only ever receive IDs.

Outstanding debt tracked in `~/life/brr/IMPROVEMENTS.md`.

## Key primitives

- `life defer <task> --reason <why>` — explicit deferral, logged to `task_mutations` with `field=defer` and reason. Does not reschedule. Use `life schedule` or `life now` to reschedule separately.
- `life now <task>` — set due=today, due_time=current time.
- `life schedule <HH:MM> <task>` — set scheduled time only.
