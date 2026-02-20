from typing import Any

from life import config
from life.db import get_db
from life.lib.errors import echo

__all__ = ["CheckResult", "cli", "score"]


def score() -> dict[str, Any]:
    if not config.DB_PATH.exists():
        return {"ok": False, "detail": "db not initialized"}
    try:
        with get_db() as conn:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            if result and result[0] == "ok":
                return {"ok": True, "detail": "db integrity ok"}
            return {"ok": False, "detail": f"integrity: {result}"}
    except Exception as e:
        return {"ok": False, "detail": f"db error: {e}"}


def cli() -> None:
    result = score()
    status = "✓" if result["ok"] else "✗"
    echo(f"db: {status} {result['detail']}")
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
