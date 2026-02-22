import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from comms.db import get_db


@dataclass
class CheckResult:
    ok: bool
    score: int
    detail: str


def _check_ci() -> CheckResult:
    just_bin = shutil.which("just")
    if not just_bin:
        return CheckResult(ok=False, score=0, detail="just not found")
    result = subprocess.run(
        [just_bin, "ci"],
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    if result.returncode != 0:
        return CheckResult(ok=False, score=0, detail=f"CI failed: {result.returncode}")
    return CheckResult(ok=True, score=100, detail="CI passed")


def _check_db_integrity() -> CheckResult:
    try:
        with get_db() as conn:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            if result and result[0] == "ok":
                return CheckResult(ok=True, score=100, detail="db integrity ok")
            return CheckResult(ok=False, score=0, detail=f"integrity: {result}")
    except Exception as e:
        return CheckResult(ok=False, score=0, detail=f"db error: {e}")


def _check_accounts_linked() -> CheckResult:
    try:
        with get_db() as conn:
            count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        if count == 0:
            return CheckResult(ok=False, score=0, detail="no accounts linked")
        return CheckResult(ok=True, score=100, detail=f"{count} accounts linked")
    except Exception:
        return CheckResult(ok=True, score=100, detail="accounts table missing (ok)")


_CHECKS: list[tuple[str, Callable[[], CheckResult], int]] = [
    ("ci", _check_ci, 50),
    ("db", _check_db_integrity, 30),
    ("accounts", _check_accounts_linked, 20),
]


def score() -> dict[str, Any]:
    results: dict[str, CheckResult] = {}
    total_weight = sum(w for _, _, w in _CHECKS)
    weighted_score = 0

    for name, check_fn, weight in _CHECKS:
        result = check_fn()
        results[name] = result
        weighted_score += (result.score / 100) * weight

    final_score = int((weighted_score / total_weight) * 100)
    all_ok = all(r.ok for r in results.values())

    return {
        "ok": all_ok,
        "score": final_score,
        "checks": {name: {"ok": r.ok, "detail": r.detail} for name, r in results.items()},
    }


def cli() -> None:
    result = score()
    sys.stdout.write(f"health: {result['score']}/100 {'✓' if result['ok'] else '✗'}\n")
    for name, check in result["checks"].items():
        status = "✓" if check["ok"] else "✗"
        sys.stdout.write(f"  {name}: {status} {check['detail']}\n")
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
