import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from queue import Empty, Queue

from fncli import cli

from .db import get_db
from .lib.ansi import strip as ansi_strip
from .lib.errors import echo, exit_error
from .lib.tail import StreamParser, format_entry


@dataclass(frozen=True)
class StewardSession:
    id: int
    summary: str
    logged_at: datetime


@dataclass(frozen=True)
class Observation:
    id: int
    body: str
    tag: str | None
    logged_at: datetime
    about_date: date | None = None


def add_session(summary: str) -> int:
    with get_db() as conn:
        cursor = conn.execute("INSERT INTO steward_sessions (summary) VALUES (?)", (summary,))
        return cursor.lastrowid or 0


def add_observation(body: str, tag: str | None = None, about_date: date | None = None) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO steward_observations (body, tag, about_date) VALUES (?, ?, ?)",
            (body, tag, about_date.isoformat() if about_date else None),
        )
        return cursor.lastrowid or 0


def get_observations(limit: int = 20, tag: str | None = None) -> list[Observation]:
    with get_db() as conn:
        if tag:
            rows = conn.execute(
                "SELECT id, body, tag, logged_at, about_date FROM steward_observations WHERE tag = ? ORDER BY logged_at DESC LIMIT ?",
                (tag, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, body, tag, logged_at, about_date FROM steward_observations ORDER BY logged_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            Observation(
                id=row[0],
                body=row[1],
                tag=row[2],
                logged_at=datetime.fromisoformat(row[3]),
                about_date=date.fromisoformat(row[4]) if row[4] else None,
            )
            for row in rows
        ]


def delete_observation(obs_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM steward_observations WHERE id = ?", (obs_id,))
        return cursor.rowcount > 0


def get_sessions(limit: int = 10) -> list[StewardSession]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, summary, logged_at FROM steward_sessions ORDER BY logged_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            StewardSession(id=row[0], summary=row[1], logged_at=datetime.fromisoformat(row[2]))
            for row in rows
        ]


def _steward_prompt() -> str:
    return """You are **Steward**. Constitution: `~/life/CLAUDE.md`. Tyson is absent. Act.

## Principle: Orient, then improve

Current state first. Then find the highest-leverage intervention.

## Principle: Forage for failure modes

Stale admin, untagged tasks, low completion rates, outdated tracking — these are your signals.

## Principle: Close loops

Every spawn must either:
1. Complete one real-world task, or
2. Improve the system that prevents task completion

## Principle: Sacred invariants

- `~/space/` is swarm domain, not yours
- `life backup` before risk
- Evidence over intuition — check the actual state

## Close

Log what you did and why. Commit atomic. Stop.

Run exactly one autonomous loop for ~/life. Make concrete progress, then stop."""


def _read_stream_lines(stream_name: str, stream, out_q: Queue[tuple[str, str | None]]) -> None:
    try:
        for line in iter(stream.readline, ""):
            out_q.put((stream_name, line))
    finally:
        out_q.put((stream_name, None))


def _run_tail_stream(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str],
    timeout: int,
    raw: bool,
    quiet_system: bool,
) -> int:
    parser = StreamParser()
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    if proc.stdout is None or proc.stderr is None:
        raise RuntimeError("subprocess streams unavailable")

    out_q: Queue[tuple[str, str | None]] = Queue()
    stdout_thread = threading.Thread(
        target=_read_stream_lines, args=("stdout", proc.stdout, out_q), daemon=True
    )
    stderr_thread = threading.Thread(
        target=_read_stream_lines, args=("stderr", proc.stderr, out_q), daemon=True
    )
    stdout_thread.start()
    stderr_thread.start()

    deadline = time.monotonic() + timeout
    stdout_done = False
    stderr_done = False
    stderr_lines: list[str] = []
    timed_out = False
    last_rendered: str | None = None

    while not (stdout_done and stderr_done):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
            break
        try:
            stream_name, line = out_q.get(timeout=min(0.2, remaining))
        except Empty:
            if proc.poll() is not None and stdout_done and stderr_done:
                break
            continue

        if line is None:
            if stream_name == "stdout":
                stdout_done = True
            else:
                stderr_done = True
            continue

        text = line.rstrip("\n")
        if stream_name == "stderr":
            if text.strip():
                stderr_lines.append(text.strip())
            continue

        if raw:
            echo(text)
            continue

        entries = parser.parse_line(text)
        for entry in entries:
            rendered = format_entry(entry, quiet_system=quiet_system)
            if not rendered:
                continue
            rendered_plain = ansi_strip(rendered).strip()
            if rendered == last_rendered and rendered_plain.startswith(("error.", "in=")):
                continue
            echo(rendered)
            last_rendered = rendered

    if timed_out:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        echo(f"[tail] timed out after {timeout}s", err=True)
        return 124

    rc = proc.wait()
    stdout_thread.join(timeout=0.2)
    stderr_thread.join(timeout=0.2)
    if rc != 0 and stderr_lines:
        echo(f"[tail] stderr: {stderr_lines[-1]}", err=True)
    return rc


def cmd_tail(
    cycles: int = 1,
    interval_seconds: int = 0,
    model: str = "glm-5",
    dry_run: bool = False,
    continue_on_error: bool = False,
    timeout_seconds: int = 1200,
    retries: int = 2,
    retry_delay_seconds: int = 2,
    raw: bool = False,
    quiet_system: bool = False,
) -> None:
    from .lib.providers import glm

    if cycles < 1:
        exit_error("--cycles must be >= 1")
    if interval_seconds < 0:
        exit_error("--every must be >= 0")
    if timeout_seconds < 1:
        exit_error("--timeout must be >= 1")
    if retries < 0:
        exit_error("--retries must be >= 0")
    if retry_delay_seconds < 0:
        exit_error("--retry-delay must be >= 0")

    life_dir = Path.home() / "life"
    prompt = _steward_prompt()

    for i in range(1, cycles + 1):
        echo(f"[tail] cycle {i}/{cycles}")
        cmd = glm.build_command(prompt=prompt)
        env = glm.build_env()
        attempts = retries + 1
        if dry_run:
            echo(" ".join(cmd))
        else:
            ok = False
            last_rc = 1
            for attempt in range(1, attempts + 1):
                if attempt > 1:
                    echo(f"[tail] retry {attempt - 1}/{retries} after failure")
                try:
                    last_rc = _run_tail_stream(
                        cmd,
                        cwd=life_dir,
                        env=env,
                        timeout=timeout_seconds,
                        raw=raw,
                        quiet_system=quiet_system,
                    )
                except Exception as exc:
                    echo(f"[tail] execution error: {exc}", err=True)
                    last_rc = 1

                if last_rc == 0:
                    ok = True
                    break
                if attempt < attempts and retry_delay_seconds > 0:
                    time.sleep(retry_delay_seconds)

            if not ok:
                if continue_on_error:
                    echo(f"[tail] cycle {i} failed (exit {last_rc}), continuing")
                else:
                    exit_error(f"tail loop failed on cycle {i} (exit {last_rc})")
        if i < cycles and interval_seconds > 0:
            echo(f"[tail] sleeping {interval_seconds}s")
            time.sleep(interval_seconds)


STEWARD_BIRTHDAY = datetime(2026, 2, 18)


@cli("life steward")
def boot():
    """Load life state and emit sitrep for interactive session start"""
    from .lib.clock import today
    from .metrics import build_feedback_snapshot, render_feedback_snapshot
    from .mood import get_recent_moods
    from .tasks import get_all_tasks, get_tasks

    age_days = (datetime.now() - STEWARD_BIRTHDAY).days
    now_local = datetime.now()
    echo(f"STEWARD — day {age_days}  |  {now_local.strftime('%a %d %b %Y  %I:%M%p').lower()}\n")

    tasks = get_tasks()
    all_tasks = get_all_tasks()
    steward_tasks = [t for t in get_tasks(include_steward=True) if t.steward]
    if steward_tasks:
        echo("STEWARD TASKS:")
        for t in steward_tasks:
            echo(f"  · {t.content}")
        echo("")
    today_date = today()
    snapshot = build_feedback_snapshot(all_tasks=all_tasks, pending_tasks=tasks, today=today_date)
    echo("\n".join(render_feedback_snapshot(snapshot)))

    sessions = get_sessions(limit=1)
    if sessions:
        s = sessions[0]
        now = datetime.now()
        secs = (now - s.logged_at).total_seconds()
        rel = _rel(secs)
        echo(f"\nLAST SESSION ({rel}): {s.summary}")

    now = datetime.now()
    today_d = date.today()
    recent = get_observations(limit=40)

    upcoming_obs = [o for o in recent if o.about_date and o.about_date >= today_d]
    recent_obs = [
        o for o in recent if not o.about_date and (now - o.logged_at).total_seconds() < 86400
    ]
    active_tags = {tag for t in tasks for tag in (getattr(t, "tags", None) or [])}
    tagged_obs: list[Observation] = []
    seen_ids: set[int] = {o.id for o in recent_obs} | {o.id for o in upcoming_obs}
    for tag in active_tags:
        for o in get_observations(limit=5, tag=tag):
            if o.id not in seen_ids and (not o.about_date or o.about_date >= today_d):
                tagged_obs.append(o)
                seen_ids.add(o.id)

    upcoming_obs_sorted = sorted(upcoming_obs, key=lambda o: o.about_date or today_d)
    all_obs = upcoming_obs_sorted + sorted(
        recent_obs + tagged_obs, key=lambda o: o.logged_at, reverse=True
    )

    if all_obs:
        echo("\nOBSERVATIONS:")
        for o in all_obs:
            if o.about_date:
                days_until = (o.about_date - today_d).days
                if days_until == 0:
                    rel = "today"
                elif days_until == 1:
                    rel = "tomorrow"
                else:
                    rel = f"in {days_until}d"
            else:
                rel = _rel((now - o.logged_at).total_seconds())
            tag_str = f" #{o.tag}" if o.tag else ""
            echo(f"  {rel:<10}  {o.body}{tag_str}")

    from .improvements import get_improvements

    open_improvements = get_improvements()
    if open_improvements:
        echo("\nIMPROVEMENTS:")
        for i in open_improvements[:5]:
            echo(f"  [{i.id}] {i.body}")

    recent_moods = get_recent_moods(hours=24)
    if recent_moods:
        latest = recent_moods[0]
        secs = (datetime.now() - latest.logged_at).total_seconds()
        rel = _rel(secs)
        bar = "█" * latest.score + "░" * (5 - latest.score)
        label_str = f"  {latest.label}" if latest.label else ""
        echo(f"\nMOOD ({rel}): {bar}  {latest.score}/5{label_str}")
        if len(recent_moods) > 1:
            echo(f"  ({len(recent_moods)} entries last 24h)")
    else:
        echo("\nMOOD: none logged — consider asking")

    repos_dir = Path.home() / "life" / "repos"
    if repos_dir.exists():
        subrepos = sorted(p for p in repos_dir.iterdir() if p.is_dir() and (p / ".git").exists())
        if subrepos:
            echo("\nSUBREPOS:")
            now_ts = time.time()
            for repo in subrepos:
                try:
                    result = subprocess.run(
                        ["git", "log", "-1", "--format=%ct %s"],
                        cwd=repo,
                        capture_output=True,
                        text=True,
                    )
                    dirty_result = subprocess.run(
                        ["git", "status", "--porcelain"],
                        cwd=repo,
                        capture_output=True,
                        text=True,
                    )
                    dirty = "~" if dirty_result.stdout.strip() else " "
                    if result.returncode == 0 and result.stdout.strip():
                        ct_str, _, msg = result.stdout.strip().partition(" ")
                        secs = now_ts - int(ct_str)
                        if secs < 3600:
                            rel = f"{int(secs // 60)}m ago"
                        elif secs < 86400:
                            rel = f"{int(secs // 3600)}h ago"
                        elif secs < 86400 * 7:
                            rel = f"{int(secs // 86400)}d ago"
                        else:
                            rel = f"{int(secs // (86400 * 7))}w ago"
                        echo(f"  {dirty} {repo.name:<16}  {rel:<10}  {msg}")
                    else:
                        echo(f"  {dirty} {repo.name:<16}  (no commits)")
                except Exception:
                    echo(f"    {repo.name:<16}  (error)")


@cli("life steward")
def close(summary: str):
    """Write session log and close interactive session"""
    add_session(summary)
    echo("→ session logged")


@cli("life steward")
def observe(
    body: str,
    tag: str | None = None,
    about: str | None = None,
):
    """Log a raw observation — things Tyson says that should persist as context"""
    from .lib.dates import parse_due_date

    about_date: date | None = None
    if about:
        parsed_str = parse_due_date(about)
        about_date = date.fromisoformat(parsed_str) if parsed_str else None

    add_observation(body, tag=tag, about_date=about_date)
    suffix = f" #{tag}" if tag else ""
    about_str = f" (about {about_date})" if about_date else ""
    echo(f"→ {body}{suffix}{about_str}")


@cli("life steward")
def rm(
    query: str | None = None,
):
    """Delete an observation — fuzzy match or latest"""
    observations = get_observations(limit=50)
    if not observations:
        exit_error("no observations to remove")

    if query is None:
        target = observations[0]
    else:
        q = query.lower()
        matches = [o for o in observations if q in o.body.lower()]
        if not matches:
            exit_error(f"no observation matching '{query}'")
        target = matches[0]

    deleted = delete_observation(target.id)
    if deleted:
        echo(f"→ removed: {target.body[:80]}")
    else:
        exit_error("delete failed")


@cli("life steward")
def dash():
    """Steward dashboard — improvements, patterns, observations, sessions"""
    from .improvements import get_improvements
    from .patterns import get_patterns

    improvements = get_improvements()
    if improvements:
        echo("IMPROVEMENTS:")
        for i in improvements:
            echo(f"  [{i.id}] {i.body}")
    else:
        echo("IMPROVEMENTS: none")

    patterns = get_patterns(limit=5)
    if patterns:
        echo("\nRECENT PATTERNS:")
        now = datetime.now()
        for p in patterns:
            s = (now - p.logged_at).total_seconds()
            rel = _rel(s) if s < 86400 * 7 else p.logged_at.strftime("%Y-%m-%d")
            echo(f"  {rel:<10}  {p.body}")

    observations = get_observations(limit=10)
    if observations:
        echo("\nRECENT OBSERVATIONS:")
        now = datetime.now()
        for o in observations:
            rel = _rel((now - o.logged_at).total_seconds())
            tag_str = f" #{o.tag}" if o.tag else ""
            echo(f"  {rel:<10}  {o.body}{tag_str}")

    sessions = get_sessions(limit=5)
    if sessions:
        echo("\nRECENT SESSIONS:")
        now_dt = datetime.now()
        for s in sessions:
            rel = _rel((now_dt - s.logged_at).total_seconds())
            echo(f"  {rel:<10}  {s.summary[:90]}")


@cli("life steward")
def improve(
    body: str | None = None,
    log: bool = False,
    done: str | None = None,
):
    """Log a system improvement or mark one done"""
    from .improvements import add_improvement, get_improvements, mark_improvement_done

    if done is not None:
        target = mark_improvement_done(done)
        if target:
            echo(f"✓ {target.body}")
        else:
            exit_error(f"no open improvement matching '{done}'")
        return

    if log or not body:
        improvements = get_improvements()
        if not improvements:
            echo("no open improvements")
            return
        now = datetime.now()
        for i in improvements:
            rel = _rel((now - i.logged_at).total_seconds())
            echo(f"  {i.id:<4} {rel:<10}  {i.body}")
        return

    add_improvement(body)
    echo(f"→ {body}")


@cli("life steward")
def log(
    limit: int = 10,
):
    """Show recent steward session logs"""
    sessions = get_sessions(limit=limit)
    if not sessions:
        echo("no sessions logged")
        return
    now = datetime.utcnow()
    for s in sessions:
        rel = _rel((now - s.logged_at).total_seconds())
        echo(f"{rel:<10}  {s.summary}")


def _rel(secs: float) -> str:
    if secs < 3600:
        return f"{int(secs // 60)}m ago"
    if secs < 86400:
        return f"{int(secs // 3600)}h ago"
    return f"{int(secs // 86400)}d ago"


def _select_required_real_world_task(tasks):
    from .lib.clock import today

    discomfort = {"finance", "legal", "janice"}
    candidates = [t for t in tasks if set(t.tags or []).intersection(discomfort)]
    if not candidates:
        return None
    overdue = [t for t in candidates if t.scheduled_date and t.scheduled_date < today()]
    ranked = overdue or candidates
    return sorted(ranked, key=lambda t: t.created)[0]


def _run_autonomous() -> None:
    from .lib.clock import today
    from .lib.providers import glm
    from .loop import (
        load_loop_state,
        require_real_world_closure,
        save_loop_state,
        update_loop_state,
    )
    from .metrics import build_feedback_snapshot, render_feedback_snapshot
    from .tasks import get_all_tasks, get_tasks

    tasks_before = get_tasks()
    all_before = get_all_tasks()
    today_date = today()
    snapshot_before = build_feedback_snapshot(
        all_tasks=all_before, pending_tasks=tasks_before, today=today_date
    )
    echo("\n".join(render_feedback_snapshot(snapshot_before)))

    state = load_loop_state()
    gate_required = require_real_world_closure(state)
    required_task = _select_required_real_world_task(tasks_before) if gate_required else None

    prompt = _steward_prompt()
    if required_task:
        prompt += (
            "\n\nHARD GATE: Before any meta/refactor work, close this real-world task in this run: "
            f"{required_task.content} ({required_task.id})."
        )
        echo(f"steward gate: close real-world loop first -> {required_task.content}")

    cmd = glm.build_command(prompt=prompt)
    env = glm.build_env()
    rc = _run_tail_stream(
        cmd,
        cwd=Path.home() / "life",
        env=env,
        timeout=1200,
        raw=False,
        quiet_system=False,
    )
    if rc != 0:
        update_loop_state(
            state,
            shipped_code=False,
            shipped_life=False,
            flags=snapshot_before.flags,
            required_task_id=required_task.id if required_task else None,
            outcome=f"tail_failed_{rc}",
        )
        save_loop_state(state)
        exit_error(f"steward loop failed (exit {rc})")

    all_after = get_all_tasks()
    tasks_after = get_tasks()
    snapshot_after = build_feedback_snapshot(
        all_tasks=all_after, pending_tasks=tasks_after, today=today_date
    )

    before_map = {t.id: t for t in all_before}
    after_map = {t.id: t for t in all_after}
    newly_completed = [
        tid
        for tid, before_task in before_map.items()
        if before_task.completed_at is None
        and tid in after_map
        and after_map[tid].completed_at is not None
    ]
    shipped_life = bool(newly_completed)

    update_loop_state(
        state,
        shipped_code=True,
        shipped_life=shipped_life,
        flags=snapshot_after.flags,
        required_task_id=required_task.id if required_task else None,
        outcome="ok" if shipped_life else "code_only",
    )
    save_loop_state(state)

    echo("\n".join(render_feedback_snapshot(snapshot_after)))
    if gate_required and not shipped_life:
        exit_error("steward gate failed: no real-world task was closed")


@cli("life")
def auto(
    cycles: int = 1,
    every: int = 0,
    model: str = "glm-4",
    timeout: int = 1200,
    retries: int = 2,
    retry_delay: int = 2,
    dry_run: bool = False,
    raw: bool = False,
    quiet_system: bool = False,
    continue_on_error: bool = False,
) -> None:
    """Run unattended Steward loop through the glm connector"""
    cmd_tail(
        cycles=cycles,
        interval_seconds=every,
        model=model,
        timeout_seconds=timeout,
        retries=retries,
        retry_delay_seconds=retry_delay,
        dry_run=dry_run,
        raw=raw,
        quiet_system=quiet_system,
        continue_on_error=continue_on_error,
    )


@cli("life steward", name="run")
def steward_run() -> None:
    """Run autonomous steward loop"""
    _run_autonomous()
