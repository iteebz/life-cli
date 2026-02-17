import contextlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .. import config

_SKIP_TABLES = {"_migrations"}


def _is_core_table(name: str) -> bool:
    return name not in _SKIP_TABLES and not ("_fts" in name or name.startswith("fts_"))


def _sqlite_backup(src: Path, dst: Path) -> None:
    src_conn = sqlite3.connect(src, timeout=30)
    dst_conn = sqlite3.connect(dst)
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()


def _row_counts(db_path: Path) -> dict[str, int]:
    try:
        conn = sqlite3.connect(str(db_path), timeout=2)
        try:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                if _is_core_table(r[0])
            ]
            counts = {}
            for table in tables:
                with contextlib.suppress(sqlite3.OperationalError):
                    counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # noqa: S608
            return counts
        finally:
            conn.close()
    except sqlite3.DatabaseError:
        return {}


def _get_previous_backup(current_path: Path) -> Path | None:
    backup_dir = config.BACKUP_DIR
    if not backup_dir.exists():
        return None
    snapshots = sorted(backup_dir.iterdir(), reverse=True)
    for s in snapshots:
        if s == current_path:
            continue
        if (s / "life.db").exists():
            return s / "life.db"
    return None


def backup() -> dict[str, Any]:
    src = config.DB_PATH
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_path = config.BACKUP_DIR / timestamp
    backup_path.mkdir(parents=True, exist_ok=True)

    dst = backup_path / "life.db"
    _sqlite_backup(src, dst)

    for suffix in ["-shm", "-wal"]:
        wal = src.parent / f"{src.stem}{suffix}"
        if wal.exists():
            import shutil
            shutil.copy2(wal, backup_path / wal.name)

    try:
        conn = sqlite3.connect(str(dst), timeout=2)
        try:
            result = conn.execute("PRAGMA integrity_check").fetchone()[0]
            integrity_ok = result == "ok"
        finally:
            conn.close()
    except Exception:
        integrity_ok = False

    current_counts = _row_counts(dst)
    total = sum(current_counts.values())

    previous_db = _get_previous_backup(backup_path)
    if previous_db and previous_db.exists():
        prev_counts = _row_counts(previous_db)
        prev_total = sum(prev_counts.values())
        delta_total = total - prev_total
        delta_by_table = {
            t: current_counts[t] - prev_counts.get(t, 0)
            for t in current_counts
            if current_counts[t] - prev_counts.get(t, 0) != 0
        }
    else:
        delta_total = None
        delta_by_table = {}

    return {
        "path": backup_path,
        "integrity_ok": integrity_ok,
        "rows": total,
        "delta_total": delta_total,
        "delta_by_table": delta_by_table,
    }
