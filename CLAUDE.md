Read ARCH.md for structure and layer boundaries.

The CLI entry point is `life/cli.py`. Domain logic lives in `life/tasks.py`, `life/habits.py` etc. Shared infrastructure is in `life/lib/`. Output via `echo()`, errors via `exit_error()` — both in `life/lib/errors.py`.

Outstanding debt tracked in `~/life/brr/IMPROVEMENTS.md`.
