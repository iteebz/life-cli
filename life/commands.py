import subprocess
import sys
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from queue import Empty, Queue

from .config import get_profile, set_profile
from .dashboard import get_pending_items, get_today_breakdown, get_today_completed
from .habits import (
    add_habit,
    archive_habit,
    delete_habit,
    get_archived_habits,
    get_checks,
    get_habits,
    toggle_check,
    update_habit,
)
from .interventions import (
    add_intervention,
    get_interventions,
)
from .interventions import (
    get_stats as get_intervention_stats,
)
from .lib.ansi import ANSI
from .lib.ansi import strip as ansi_strip
from .lib.clock import now, today
from .lib.dates import add_date, list_dates, parse_due_date, remove_date
from .lib.errors import echo, exit_error
from .lib.format import format_status
from .lib.parsing import parse_due_and_item, parse_time, validate_content
from .lib.providers import glm
from .lib.render import render_dashboard, render_habit_matrix, render_momentum, render_task_detail
from .lib.resolve import (
    resolve_habit,
    resolve_item,
    resolve_item_any,
    resolve_item_exact,
    resolve_task,
)
from .lib.tail import StreamParser, format_entry
from .loop import (
    load_loop_state,
    require_real_world_closure,
    save_loop_state,
    update_loop_state,
)
from .metrics import build_feedback_snapshot, render_feedback_snapshot
from .models import Task
from .momentum import weekly_momentum
from .patterns import add_pattern, delete_pattern, get_patterns
from .steward import Observation
from .tags import add_tag, remove_tag
from .tasks import (
    UNSET,
    add_link,
    add_task,
    cancel_task,
    check_task,
    defer_task,
    delete_task,
    get_all_tasks,
    get_links,
    get_mutations,
    get_subtasks,
    get_tasks,
    last_completion,
    remove_link,
    set_blocked_by,
    toggle_focus,
    uncheck_task,
    update_task,
)

__all__ = [
    "cmd_archive",
    "cmd_block",
    "cmd_cancel",
    "cmd_check",
    "cmd_dashboard",
    "cmd_dates",
    "cmd_defer",
    "cmd_done",
    "cmd_due",
    "cmd_focus",
    "cmd_habit",
    "cmd_habits",
    "cmd_link",
    "cmd_momentum",
    "cmd_mood",
    "cmd_now",
    "cmd_pattern",
    "cmd_profile",
    "cmd_rename",
    "cmd_rm",
    "cmd_schedule",
    "cmd_set",
    "cmd_show",
    "cmd_stats",
    "cmd_status",
    "cmd_steward",
    "cmd_steward_boot",
    "cmd_steward_close",
    "cmd_steward_dash",
    "cmd_tag",
    "cmd_tail",
    "cmd_task",
    "cmd_today",
    "cmd_tomorrow",
    "cmd_track",
    "cmd_unblock",
    "cmd_uncheck",
    "cmd_unfocus",
    "cmd_unlink",
    "cmd_untag",
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


def _select_required_real_world_task(tasks: list[Task]) -> Task | None:
    discomfort = {"finance", "legal", "janice"}
    candidates = [t for t in tasks if set(t.tags or []).intersection(discomfort)]
    if not candidates:
        return None

    overdue = [t for t in candidates if t.due_date and t.due_date < today()]
    ranked = overdue or candidates
    return sorted(ranked, key=lambda t: t.created)[0]


def _task_map(tasks: list[Task]) -> dict[str, Task]:
    return {t.id: t for t in tasks}


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


def cmd_set(
    args: list[str],
    parent: str | None = None,
    content: str | None = None,
    description: str | None = None,
) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life set <task> [-p parent] [-c content]")
    task = resolve_task(ref)
    parent_id: str | None = None
    has_update = False
    if parent is not None:
        parent_task = resolve_task(parent)
        if parent_task.parent_id:
            exit_error("Error: subtasks cannot have subtasks")
        if parent_task.id == task.id:
            exit_error("Error: a task cannot be its own parent")
        if task.focus:
            exit_error("Error: cannot parent a focused task — unfocus first")
        parent_id = parent_task.id
        has_update = True
    if content is not None:
        if not content.strip():
            exit_error("Error: content cannot be empty")
        has_update = True
    desc: str | None = None
    if description is not None:
        desc = description if description != "" else None
        has_update = True
    if not has_update:
        exit_error("Nothing to set. Use -p for parent, -c for content, or -d for description.")
    update_task(
        task.id,
        content=content,
        parent_id=parent_id if parent is not None else UNSET,
        description=desc if description is not None else UNSET,
    )
    updated = resolve_task(content or ref)
    prefix = "  └ " if updated.parent_id else ""
    echo(f"{prefix}{format_status('□', updated.content, updated.id)}")


def cmd_show(args: list[str]) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life show <task>")
    task = resolve_task(ref)
    subtasks = get_subtasks(task.id)
    linked = get_links(task.id)
    mutations = get_mutations(task.id)
    echo(render_task_detail(task, subtasks, linked, mutations))


def cmd_link(a_args: list[str], b_args: list[str]) -> None:
    a = resolve_task(" ".join(a_args))
    b = resolve_task(" ".join(b_args))
    if a.id == b.id:
        exit_error("Cannot link a task to itself")
    add_link(a.id, b.id)
    echo(f"{a.content.lower()} {ANSI.GREY}~ {b.content.lower()}{ANSI.RESET}")


def cmd_unlink(a_args: list[str], b_args: list[str]) -> None:
    a = resolve_task(" ".join(a_args))
    b = resolve_task(" ".join(b_args))
    remove_link(a.id, b.id)
    echo(f"{a.content.lower()} {ANSI.GREY}✗ {b.content.lower()}{ANSI.RESET}")


def cmd_block(blocked_args: list[str], blocker_args: list[str]) -> None:
    blocked_ref = " ".join(blocked_args)
    blocker_ref = " ".join(blocker_args)
    blocked = resolve_task(blocked_ref)
    blocker = resolve_task(blocker_ref)
    if blocker.id == blocked.id:
        exit_error("A task cannot block itself")
    set_blocked_by(blocked.id, blocker.id)
    echo(f"⊘ {blocked.content.lower()}  ←  {blocker.content.lower()}")


def cmd_unblock(args: list[str]) -> None:
    task = resolve_task(" ".join(args))
    if not task.blocked_by:
        exit_error(f"'{task.content}' is not blocked")
    set_blocked_by(task.id, None)
    echo(f"□ {task.content.lower()}  unblocked")


def cmd_mood(
    score: int | None = None,
    label: str | None = None,
    show: bool = False,
) -> None:
    from .mood import add_mood, get_recent_moods

    if show or score is None:
        entries = get_recent_moods(hours=24)
        if not entries:
            echo("no mood logged in the last 24h")
            return
        now_dt = datetime.now()
        for e in entries:
            delta = now_dt - e.logged_at
            secs = delta.total_seconds()
            if secs < 3600:
                rel = f"{int(secs // 60)}m ago"
            elif secs < 86400:
                rel = f"{int(secs // 3600)}h ago"
            else:
                rel = f"{int(secs // 86400)}d ago"
            bar = "█" * e.score + "░" * (5 - e.score)
            label_str = f"  {e.label}" if e.label else ""
            echo(f"  {rel:<10}  {bar}  {e.score}/5{label_str}")
        return

    if score < 1 or score > 5:
        exit_error("Score must be 1-5")
    add_mood(score, label)
    bar = "█" * score + "░" * (5 - score)
    label_str = f"  {label}" if label else ""
    echo(f"→ {bar}  {score}/5{label_str}")


STEWARD_BIRTHDAY = datetime(2026, 2, 18)


def cmd_steward_boot() -> None:
    from .steward import get_sessions

    age_days = (datetime.now() - STEWARD_BIRTHDAY).days
    now_local = datetime.now()
    echo(f"STEWARD — day {age_days}  |  {now_local.strftime('%a %d %b %Y  %I:%M%p').lower()}\n")

    tasks = get_tasks()
    all_tasks = get_all_tasks()
    today_date = today()
    snapshot = build_feedback_snapshot(all_tasks=all_tasks, pending_tasks=tasks, today=today_date)
    echo("\n".join(render_feedback_snapshot(snapshot)))
    sessions = get_sessions(limit=1)
    if sessions:
        s = sessions[0]
        now = datetime.now()
        delta = now - s.logged_at
        secs = delta.total_seconds()
        if secs < 3600:
            rel = f"{int(secs // 60)}m ago"
        elif secs < 86400:
            rel = f"{int(secs // 3600)}h ago"
        else:
            rel = f"{int(secs // 86400)}d ago"
        echo(f"\nLAST SESSION ({rel}): {s.summary}")

    steward_tasks = get_tasks(include_steward=True)
    steward_tasks = [t for t in steward_tasks if t.steward]
    if steward_tasks:
        echo("\nSTEWARD IN PROGRESS:")
        for t in steward_tasks[:3]:
            echo(f"  → {t.content}")

    from datetime import date

    from .steward import get_observations

    now = datetime.now()
    today_d = date.today()
    recent = get_observations(limit=40)
    cutoff_24h = 86400

    upcoming_obs = [o for o in recent if o.about_date and o.about_date >= today_d]
    recent_obs = [
        o for o in recent if not o.about_date and (now - o.logged_at).total_seconds() < cutoff_24h
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
                delta = now - o.logged_at
                secs = delta.total_seconds()
                if secs < 3600:
                    rel = f"{int(secs // 60)}m ago"
                elif secs < 86400:
                    rel = f"{int(secs // 3600)}h ago"
                else:
                    rel = f"{int(secs // 86400)}d ago"
            tag_str = f" #{o.tag}" if o.tag else ""
            echo(f"  {rel:<10}  {o.body}{tag_str}")

    from .mood import get_recent_moods

    recent_moods = get_recent_moods(hours=24)
    if recent_moods:
        latest = recent_moods[0]
        now_dt = datetime.now()
        delta = now_dt - latest.logged_at
        secs = delta.total_seconds()
        if secs < 3600:
            rel = f"{int(secs // 60)}m ago"
        elif secs < 86400:
            rel = f"{int(secs // 3600)}h ago"
        else:
            rel = f"{int(secs // 86400)}d ago"
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


def cmd_steward_close(summary: str) -> None:
    from .steward import add_session

    add_session(summary)
    echo("→ session logged")


def cmd_steward_dash() -> None:
    from .patterns import get_patterns
    from .steward import get_observations

    steward_tasks = get_tasks(include_steward=True)
    steward_tasks = [t for t in steward_tasks if t.steward]

    if steward_tasks:
        echo("STEWARD TASKS:")
        for t in steward_tasks:
            status = "✓" if t.completed_at else "□"
            echo(f"  {status} {t.content}")
    else:
        echo("STEWARD TASKS: none")

    patterns = get_patterns(limit=5)
    if patterns:
        echo("\nRECENT PATTERNS:")
        now = datetime.now()
        for p in patterns:
            delta = now - p.logged_at
            s = delta.total_seconds()
            if s < 3600:
                rel = f"{int(s // 60)}m ago"
            elif s < 86400:
                rel = f"{int(s // 3600)}h ago"
            elif s < 86400 * 7:
                rel = f"{int(s // 86400)}d ago"
            else:
                rel = p.logged_at.strftime("%Y-%m-%d")
            echo(f"  {rel:<10}  {p.body}")

    observations = get_observations(limit=10)
    if observations:
        echo("\nRECENT OBSERVATIONS:")
        now = datetime.now()
        for o in observations:
            delta = now - o.logged_at
            s = delta.total_seconds()
            if s < 3600:
                rel = f"{int(s // 60)}m ago"
            elif s < 86400:
                rel = f"{int(s // 3600)}h ago"
            else:
                rel = f"{int(s // 86400)}d ago"
            tag_str = f" #{o.tag}" if o.tag else ""
            echo(f"  {rel:<10}  {o.body}{tag_str}")

    from .steward import get_sessions

    sessions = get_sessions(limit=5)
    if sessions:
        echo("\nRECENT SESSIONS:")
        now_dt = datetime.now()
        for s in sessions:
            delta = now_dt - s.logged_at
            secs = delta.total_seconds()
            if secs < 3600:
                rel = f"{int(secs // 60)}m ago"
            elif secs < 86400:
                rel = f"{int(secs // 3600)}h ago"
            else:
                rel = f"{int(secs // 86400)}d ago"
            echo(f"  {rel:<10}  {s.summary[:90]}")


def cmd_steward() -> None:
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

    before_map = _task_map(all_before)
    after_map = _task_map(all_after)
    newly_completed = [
        tid
        for tid, before_task in before_map.items()
        if before_task.completed_at is None
        and tid in after_map
        and after_map[tid].completed_at is not None
    ]
    shipped_life = bool(newly_completed)
    shipped_code = True

    update_loop_state(
        state,
        shipped_code=shipped_code,
        shipped_life=shipped_life,
        flags=snapshot_after.flags,
        required_task_id=required_task.id if required_task else None,
        outcome="ok" if shipped_life else "code_only",
    )
    save_loop_state(state)

    echo("\n".join(render_feedback_snapshot(snapshot_after)))
    if gate_required and not shipped_life:
        exit_error("steward gate failed: no real-world task was closed")


def cmd_track(
    description: str | None = None,
    result: str | None = None,
    note: str | None = None,
    show_stats: bool = False,
    show_log: bool = False,
) -> None:
    if show_stats:
        stats = get_intervention_stats()
        total = sum(stats.values())
        if not total:
            echo("no interventions logged")
            return
        won = stats.get("won", 0)
        lost = stats.get("lost", 0)
        deferred = stats.get("deferred", 0)
        win_rate = int((won / total) * 100) if total else 0
        echo(
            f"won: {won}  lost: {lost}  deferred: {deferred}  total: {total}  win_rate: {win_rate}%"
        )
        return

    if show_log:
        interventions = get_interventions(20)
        if not interventions:
            echo("no interventions logged")
            return
        for intervention in interventions:
            ts = intervention.timestamp.strftime("%m-%d %H:%M")
            note_str = f"  ({intervention.note})" if intervention.note else ""
            echo(f"{ts}  {intervention.result:<8}  {intervention.description}{note_str}")
        return

    if not description or not result:
        exit_error("Usage: life track <description> --won|--lost|--deferred [--note 'text']")

    if result not in ("won", "lost", "deferred"):
        exit_error("Result must be --won, --lost, or --deferred")

    add_intervention(description, result, note)
    symbol = {"won": "✓", "lost": "✗", "deferred": "→"}[result]
    echo(f"{symbol} {description}")


def cmd_pattern(
    body: str | None = None,
    show_log: bool = False,
    limit: int = 20,
    rm: str | None = None,
) -> None:
    if rm is not None:
        patterns = get_patterns(limit=50)
        if not patterns:
            exit_error("no patterns to remove")
        if rm == "":
            target = patterns[0]
        else:
            q = rm.lower()
            matches = [p for p in patterns if q in p.body.lower()]
            if not matches:
                exit_error(f"no pattern matching '{rm}'")
            target = matches[0]
        deleted = delete_pattern(target.id)
        if deleted:
            echo(f"→ removed: {target.body[:80]}")
        else:
            exit_error("delete failed")
        return

    if show_log:
        patterns = get_patterns(limit)
        if not patterns:
            echo("no patterns logged")
            return
        now = datetime.now()
        for p in patterns:
            delta = now - p.logged_at
            s = delta.total_seconds()
            if s < 3600:
                rel = f"{int(s // 60)}m ago"
            elif s < 86400:
                rel = f"{int(s // 3600)}h ago"
            elif s < 86400 * 7:
                rel = f"{int(s // 86400)}d ago"
            else:
                rel = p.logged_at.strftime("%Y-%m-%d")
            echo(f"{rel:<10}  {p.body}")
        return

    if not body:
        exit_error('Usage: life pattern "observation" or life pattern --log')

    add_pattern(body)
    echo(f"→ {body}")


def cmd_dashboard(verbose: bool = False) -> None:
    items = get_pending_items() + get_habits()
    today_items = get_today_completed()
    today_breakdown = get_today_breakdown()
    echo(render_dashboard(items, today_breakdown, None, None, today_items, verbose=verbose))


def cmd_task(
    content_args: list[str],
    focus: bool = False,
    due: str | None = None,
    tags: list[str] | None = None,
    under: str | None = None,
    description: str | None = None,
    done: bool = False,
    steward: bool = False,
    source: str | None = None,
) -> None:
    content = " ".join(content_args) if content_args else ""
    try:
        validate_content(content)
    except ValueError as e:
        exit_error(f"Error: {e}")
    resolved_due = parse_due_date(due) if due else None
    parent_id = None
    if under:
        parent_task = resolve_task(under)
        if parent_task.parent_id:
            exit_error("Error: subtasks cannot have subtasks")
        parent_id = parent_task.id
    if focus and parent_id:
        exit_error("Error: cannot focus a subtask — set focus on the parent")
    task_id = add_task(
        content,
        focus=focus,
        due=resolved_due,
        tags=tags,
        parent_id=parent_id,
        description=description,
        steward=steward,
        source=source,
    )
    if done:
        check_task(task_id)
        echo(format_status("✓", content, task_id))
        return
    symbol = f"{ANSI.BOLD}⦿{ANSI.RESET}" if focus else "□"
    prefix = "  └ " if parent_id else ""
    echo(f"{prefix}{format_status(symbol, content, task_id)}")


def cmd_habit(content_args: list[str], tags: list[str] | None = None) -> None:
    content = " ".join(content_args) if content_args else ""
    try:
        validate_content(content)
    except ValueError as e:
        exit_error(f"Error: {e}")
    habit_id = add_habit(content, tags=tags)
    echo(format_status("□", content, habit_id))


def _animate_check(label: str) -> None:
    sys.stdout.write(f"  □ {label}")
    sys.stdout.flush()
    time.sleep(0.18)
    sys.stdout.write(f"\r  {ANSI.GREEN}✓{ANSI.RESET} {ANSI.GREY}{label}{ANSI.RESET}\n")
    sys.stdout.flush()


def _animate_uncheck(label: str) -> None:
    sys.stdout.write(f"  {ANSI.GREY}✓{ANSI.RESET} {label}")
    sys.stdout.flush()
    time.sleep(0.18)
    sys.stdout.write(f"\r  □ {label}\n")
    sys.stdout.flush()


def cmd_check(args: list[str]) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life check <item>")
    task, habit = resolve_item_any(ref)
    if habit:
        updated = toggle_check(habit.id)
        if updated:
            checked_today = any(c.date() == today() for c in updated.checks)
            if checked_today:
                _animate_check(habit.content.lower())
    elif task:
        if task.completed_at:
            exit_error(f"'{task.content}' is already done")
        _, parent_completed = check_task(task.id)
        _animate_check(task.content.lower())
        if parent_completed:
            _animate_check(parent_completed.content.lower())


def cmd_uncheck(args: list[str]) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life uncheck <item>")
    task, habit = resolve_item_any(ref)
    if habit:
        today_date = today()
        checks = get_checks(habit.id)
        checked_today = any(c.date() == today_date for c in checks)
        if not checked_today:
            exit_error(f"'{habit.content}' is not checked today")
        updated = toggle_check(habit.id)
        if updated:
            checked_today = any(c.date() == today() for c in updated.checks)
            if not checked_today:
                _animate_uncheck(habit.content.lower())
    elif task:
        if not task.completed_at:
            exit_error(f"'{task.content}' is not done")
        uncheck_task(task.id)
        _animate_uncheck(task.content.lower())


def cmd_done(args: list[str]) -> None:
    cmd_check(args)


def cmd_rm(args: list[str]) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life rm <item>")
    task, habit = resolve_item_any(ref)
    if task:
        delete_task(task.id)
        echo(f"{ANSI.DIM}{task.content}{ANSI.RESET}")
    elif habit:
        delete_habit(habit.id)
        echo(f"{ANSI.DIM}{habit.content}{ANSI.RESET}")


def cmd_focus(args: list[str]) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life focus <item>")
    task = resolve_task(ref)
    toggle_focus(task.id)
    symbol = f"{ANSI.BOLD}⦿{ANSI.RESET}" if not task.focus else "□"
    echo(format_status(symbol, task.content, task.id))


def cmd_unfocus(args: list[str]) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life unfocus <item>")
    task = resolve_task(ref)
    if not task.focus:
        exit_error(f"'{task.content}' is not focused")
    toggle_focus(task.id)
    echo(format_status("□", task.content, task.id))


def cmd_due(args: list[str], remove: bool = False) -> None:
    try:
        date_str, item_name = parse_due_and_item(args, remove=remove)
    except ValueError as e:
        exit_error(str(e))
    task = resolve_task(item_name)
    if remove:
        update_task(task.id, due=None)
        echo(format_status("□", task.content, task.id))
    elif date_str:
        update_task(task.id, due=date_str)
        from datetime import date as _date

        from .lib.clock import today as _today

        _due = _date.fromisoformat(date_str)
        _delta = (_due - _today()).days
        echo(format_status(f"{ANSI.GREY}+{_delta}d{ANSI.RESET}", task.content, task.id))
    else:
        exit_error(
            "Due date required (today, tomorrow, day name, or YYYY-MM-DD) or use -r/--remove to clear"
        )


def cmd_rename(from_args: list[str], to_content: str) -> None:
    if not to_content:
        exit_error("Error: 'to' content cannot be empty.")
    ref = " ".join(from_args) if from_args else ""
    task, habit = resolve_item(ref)
    item = task or habit
    if not item:
        exit_error("Error: Item not found.")
    if item.content == to_content:
        exit_error(f"Error: Cannot rename '{item.content}' to itself.")
    if isinstance(item, Task):
        update_task(item.id, content=to_content)
    else:
        update_habit(item.id, content=to_content)
    echo(f"→ {to_content}")


def cmd_untag(tag_name: str | None, args: list[str] | None, tag_opt: str | None = None) -> None:
    cmd_tag(tag_name, args, tag_opt=tag_opt, remove=True)


def cmd_tag(
    tag_name: str | None,
    args: list[str] | None,
    tag_opt: str | None = None,
    remove: bool = False,
) -> None:
    positionals = args or []
    if tag_opt:
        tag_name_final = tag_opt
        item_ref = " ".join(positionals)
    else:
        if not positionals or len(positionals) < 2:
            exit_error('Usage: life tag "ITEM" TAG  or  life tag "ITEM" --tag TAG')
        tag_name_final = positionals[-1]
        item_ref = " ".join(positionals[:-1])
    task, habit = resolve_item_exact(item_ref)
    if task:
        if remove:
            remove_tag(task.id, None, tag_name_final)
            echo(f"{task.content} ← {ANSI.GREY}#{tag_name_final}{ANSI.RESET}")
        else:
            add_tag(task.id, None, tag_name_final)
            echo(f"{task.content} {ANSI.GREY}#{tag_name_final}{ANSI.RESET}")
    elif habit:
        if remove:
            remove_tag(None, habit.id, tag_name_final)
            echo(f"{habit.content} ← {ANSI.GREY}#{tag_name_final}{ANSI.RESET}")
        else:
            add_tag(None, habit.id, tag_name_final)
            echo(f"{habit.content} {ANSI.GREY}#{tag_name_final}{ANSI.RESET}")


def cmd_archive(args: list[str], show_list: bool = False) -> None:
    if show_list:
        habits = get_archived_habits()
        if not habits:
            echo("no archived habits")
            return
        for habit in habits:
            archived = habit.archived_at.strftime("%Y-%m-%d") if habit.archived_at else "?"
            echo(f"{ANSI.DIM}{habit.content}{ANSI.RESET}  archived {archived}")
        return
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life archive <habit>")
    habit = resolve_habit(ref)
    archive_habit(habit.id)
    echo(f"{ANSI.DIM}{habit.content}{ANSI.RESET}  archived")


def cmd_habits() -> None:
    echo(render_habit_matrix(get_habits()))


def cmd_profile(profile_text: str | None = None) -> None:
    if profile_text:
        set_profile(profile_text)
        echo(f"Profile set to: {profile_text}")
    else:
        echo(get_profile() or "No profile set")


def cmd_dates(
    action: str | None = None,
    name: str | None = None,
    date_str: str | None = None,
    emoji: str = "📌",
) -> None:
    if not action:
        dates_list = list_dates()
        if dates_list:
            for date_item in dates_list:
                echo(f"{date_item.get('emoji', '📌')} {date_item['name']} - {date_item['date']}")
        else:
            echo("No dates set")
        return
    if action == "add":
        if not name or not date_str:
            exit_error("Error: add requires name and date (YYYY-MM-DD)")
        add_date(name, date_str, emoji)
        echo(f"Added date: {emoji} {name} on {date_str}")
    elif action == "remove":
        if not name:
            exit_error("Error: remove requires a date name")
        remove_date(name)
        echo(f"Removed date: {name}")
    else:
        exit_error(
            f"Error: unknown action '{action}'. Use 'add', 'remove', or no argument to list."
        )


def _format_elapsed(dt) -> str:
    delta = now() - dt
    s = int(delta.total_seconds())
    if s < 60:
        return f"{s}s ago"
    m = s // 60
    if m < 60:
        return f"{m}m ago"
    h = m // 60
    if h < 24:
        return f"{h}h ago"
    d = h // 24
    return f"{d}d ago"


def cmd_status() -> None:
    tasks = get_tasks()
    all_tasks = get_all_tasks()
    habits = get_habits()
    today_date = today()

    untagged = [t for t in tasks if not t.tags]
    overdue = [t for t in tasks if t.due_date and t.due_date < today_date]
    janice = [t for t in tasks if "janice" in (t.tags or [])]
    focused = [t for t in tasks if t.focus]

    snapshot = build_feedback_snapshot(all_tasks=all_tasks, pending_tasks=tasks, today=today_date)

    lc = last_completion()
    last_check_str = _format_elapsed(lc) if lc else "never"

    lines = []
    lines.append(
        f"tasks: {len(tasks)}  habits: {len(habits)}  focused: {len(focused)}  last check: {last_check_str}"
    )
    lines.append("\nHEALTH:")
    lines.append(f"  untagged: {len(untagged)}")
    lines.append(f"  overdue: {len(overdue)}")
    lines.append(f"  janice_open: {len(janice)}")
    lines.append("\nFLAGS:")
    if snapshot.flags:
        lines.append("  " + ", ".join(snapshot.flags))
    else:
        lines.append("  none")
    lines.append("\nHOT LIST:")
    overdue_ids = {t.id for t in overdue}
    hot_overdue = overdue[:3]
    hot_janice = [t for t in janice if t.id not in overdue_ids][:3]
    lines.extend(f"  ! {t.content}" for t in hot_overdue)
    lines.extend(f"  ♥ {t.content}" for t in hot_janice)

    if not hot_overdue and not hot_janice:
        lines.append("  none")

    echo("\n".join(lines))


def cmd_stats() -> None:
    tasks = get_tasks()
    all_tasks = get_all_tasks()
    today_date = today()
    snapshot = build_feedback_snapshot(all_tasks=all_tasks, pending_tasks=tasks, today=today_date)
    echo("\n".join(render_feedback_snapshot(snapshot)))


def cmd_momentum() -> None:
    echo(render_momentum(weekly_momentum()))


def _set_due_relative(args: list[str], offset_days: int, label: str) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error(f"Usage: life {label} <task>")
    task = resolve_task(ref)
    new_due = today() + timedelta(days=offset_days)
    was_overdue = task.due_date is not None and task.due_date < today()
    update_task(task.id, due=new_due.isoformat())
    if was_overdue:
        defer_task(task.id, "overdue_reset")
    echo(format_status("□", task.content, task.id))


def cmd_today(args: list[str]) -> None:
    _set_due_relative(args, 0, "today")


def cmd_tomorrow(args: list[str]) -> None:
    _set_due_relative(args, 1, "tomorrow")


def cmd_cancel(args: list[str], reason: str | None) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life cancel <task> --reason <why>")
    if not reason:
        exit_error("--reason required. Why are you cancelling this?")
    task = resolve_task(ref)
    cancel_task(task.id, reason)
    echo(f"✗ {task.content.lower()} — {reason}")


def cmd_defer(args: list[str], reason: str | None) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life defer <task> --reason <why>")
    if not reason:
        exit_error("--reason required. Why are you deferring this?")
    task = resolve_task(ref)
    defer_task(task.id, reason)
    echo(f"→ {task.content.lower()} deferred: {reason}")


def cmd_now(args: list[str]) -> None:
    ref = " ".join(args) if args else ""
    if not ref:
        exit_error("Usage: life now <task>")
    task = resolve_task(ref)
    current = now()
    due_str = today().isoformat()
    time_str = current.strftime("%H:%M")
    update_task(task.id, due=due_str, due_time=time_str)
    echo(format_status(f"{ANSI.GREY}{time_str}{ANSI.RESET}", task.content.lower(), task.id))


def cmd_schedule(args: list[str], remove: bool = False) -> None:
    if not args:
        exit_error("Usage: life schedule <HH:MM> <task> | life schedule -r <task>")
    if remove:
        task = resolve_task(" ".join(args))
        update_task(task.id, due_time=None)
        echo(format_status("□", task.content, task.id))
        return
    time_str = args[0]
    ref = " ".join(args[1:])
    if not ref:
        exit_error("Usage: life schedule <HH:MM> <task>")
    try:
        parsed = parse_time(time_str)
    except ValueError as e:
        exit_error(str(e))
    task = resolve_task(ref)
    update_task(task.id, due_time=parsed)
    echo(format_status(f"{ANSI.GREY}{parsed}{ANSI.RESET}", task.content, task.id))
