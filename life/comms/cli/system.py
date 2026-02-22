"""System commands: init, backup, status, inbox, triage."""

from datetime import datetime
from typing import Any

import typer

from life.comms import accounts as accts_module
from life.comms import db, services
from life.comms.adapters.email import gmail, outlook

app = typer.Typer()


def show_dashboard() -> None:
    accounts = accts_module.list_accounts("email")
    total_inbox = 0

    for account in accounts:
        if account["provider"] == "gmail":
            count = gmail.count_inbox_threads(account["email"])
            total_inbox += count
        elif account["provider"] == "outlook":
            count = outlook.count_inbox_threads(account["email"])
            total_inbox += count

    with db.get_db() as conn:
        pending_drafts = conn.execute(
            "SELECT COUNT(*) FROM drafts WHERE approved_at IS NULL AND sent_at IS NULL"
        ).fetchone()[0]
        approved_unsent = conn.execute(
            "SELECT COUNT(*) FROM drafts WHERE approved_at IS NOT NULL AND sent_at IS NULL"
        ).fetchone()[0]

    typer.echo("Comms Dashboard\n")
    typer.echo(f"Inbox threads: {total_inbox}")
    typer.echo(f"Pending drafts: {pending_drafts}")
    typer.echo(f"Approved (unsent): {approved_unsent}")


@app.command()
def inbox(limit: int = typer.Option(20, "--limit", "-n")) -> None:
    """Unified inbox (email + signal, sorted by time)"""
    items = services.get_unified_inbox(limit=limit)
    if not items:
        typer.echo("Inbox empty")
        return

    for item in items:
        ts = datetime.fromtimestamp(item.timestamp / 1000).strftime("%m-%d %H:%M")
        unread = "●" if item.unread else " "
        source = "📧" if item.source == "email" else "💬"
        typer.echo(f"{unread} {source} [{ts}] {item.sender[:20]:20} {item.preview}")


@app.command()
def init() -> None:
    """Initialize comms database and config"""
    db.init()
    typer.echo("Initialized comms database")


@app.command()
def backup() -> None:
    """Backup database to ~/.comms_backups/{timestamp}/"""
    backup_path = db.backup_db()
    if backup_path:
        typer.echo(f"Backup created: {backup_path}")
    else:
        typer.echo("No database to backup")


@app.command()
def rules() -> None:
    """Show triage rules (edit at ~/.comms/rules.md)"""
    from life.comms.config import RULES_PATH

    if not RULES_PATH.exists():
        typer.echo(f"No rules file. Create one at: {RULES_PATH}")
        return

    typer.echo(RULES_PATH.read_text())


@app.command()
def contacts() -> None:
    """Show contact notes (edit at ~/.comms/contacts.md)"""
    from life.comms.contacts import CONTACTS_PATH, get_all_contacts

    if not CONTACTS_PATH.exists():
        typer.echo(f"No contacts file. Create one at: {CONTACTS_PATH}")
        typer.echo("\nExample format:")
        typer.echo("## boss@company.com")
        typer.echo("tags: important, work")
        typer.echo("Always respond promptly. CC their assistant on big decisions.")
        typer.echo("\n## *@newsletter.com")
        typer.echo("tags: newsletter")
        typer.echo("Archive without reading.")
        return

    all_contacts = get_all_contacts()
    if not all_contacts:
        typer.echo(f"Contacts file empty. Edit at: {CONTACTS_PATH}")
        return

    for c in all_contacts:
        tags = f" [{', '.join(c.tags)}]" if c.tags else ""
        typer.echo(f"{c.pattern}{tags}")
        typer.echo(f"  {c.notes}")
        typer.echo()


@app.command()
def templates(
    init: bool = typer.Option(False, "--init", help="Create default templates file"),
) -> None:
    """Show reply templates (edit at ~/.comms/templates.md)"""
    from life.comms.templates import TEMPLATES_PATH, get_templates, init_templates

    if init:
        init_templates()
        typer.echo(f"Created templates at: {TEMPLATES_PATH}")
        return

    all_templates = get_templates()
    if not all_templates:
        typer.echo("No templates. Run `comms templates --init` to create defaults.")
        return

    for t in all_templates:
        typer.echo(f"## {t.name}")
        typer.echo(f"  {t.body[:60]}...")
        typer.echo()


@app.command()
def status() -> None:
    """Show system status"""
    from life.comms.config import get_policy

    pol = get_policy()
    typer.echo("Policy:")
    typer.echo(f"  Require approval: {pol.get('require_approval', True)}")
    typer.echo(f"  Max daily sends: {pol.get('max_daily_sends', 50)}")
    allowed_recipients: list[Any] = pol.get("allowed_recipients") or []
    allowed_domains: list[Any] = pol.get("allowed_domains") or []
    typer.echo(f"  Allowed recipients: {len(allowed_recipients)}")
    typer.echo(f"  Allowed domains: {len(allowed_domains)}")

    auto: dict[str, Any] = pol.get("auto_approve") or {}
    typer.echo("\nAuto-approve:")
    typer.echo(f"  Enabled: {auto.get('enabled', False)}")
    typer.echo(f"  Threshold: {auto.get('threshold', 0.95):.0%}")
    typer.echo(f"  Min samples: {auto.get('min_samples', 10)}")
    typer.echo(f"  Actions: {auto.get('actions', []) or 'all'}")


@app.command()
def auto_approve(
    enable: bool | None = typer.Option(None, "--enable/--disable", help="Enable or disable"),
    threshold: float | None = typer.Option(None, "--threshold", "-t", help="Accuracy threshold"),
    min_samples: int | None = typer.Option(None, "--min-samples", "-n", help="Minimum samples"),
    action: list[str] | None = None,
) -> None:
    """Configure auto-approve settings"""
    from life.comms.config import get_policy, set_policy

    pol = get_policy()
    auto: dict[str, Any] = pol.get("auto_approve") or {}

    if enable is not None:
        auto["enabled"] = enable
    if threshold is not None:
        auto["threshold"] = threshold
    if min_samples is not None:
        auto["min_samples"] = min_samples
    if action:
        auto["actions"] = list(action)

    pol["auto_approve"] = auto
    set_policy(pol)

    typer.echo(f"Auto-approve: {'enabled' if auto.get('enabled') else 'disabled'}")
    typer.echo(f"  Threshold: {auto.get('threshold', 0.95):.0%}")
    typer.echo(f"  Min samples: {auto.get('min_samples', 10)}")
    typer.echo(f"  Actions: {auto.get('actions', []) or 'all'}")


@app.command()
def stats() -> None:
    """Show learning stats from decisions"""
    from life.comms import learning

    action_stats = learning.get_decision_stats()
    if not action_stats:
        typer.echo("No decision data yet")
        return

    typer.echo("Action Stats:")
    for action, s in sorted(action_stats.items(), key=lambda x: -x[1].total):
        typer.echo(
            f"  {action:12} | {s.total:3} total | {s.accuracy:.0%} accuracy | "
            f"{s.approved} approved, {s.rejected} rejected, {s.corrected} corrected"
        )

    patterns = learning.get_correction_patterns()
    if patterns:
        typer.echo("\nCorrection Patterns:")
        for p in patterns[:5]:
            typer.echo(f"  {p['original']} → {p['corrected']} ({p['count']}x)")

    suggestions = learning.suggest_auto_approve()
    if suggestions:
        typer.echo(f"\nAuto-approve candidates (≥95% accuracy, ≥10 samples): {suggestions}")


@app.command()
def senders(limit: int = typer.Option(20, "--limit", "-n")) -> None:
    """Show sender statistics and priority scores"""
    from life.comms import senders

    top = senders.get_top_senders(limit=limit)
    if not top:
        typer.echo("No sender data yet")
        return

    typer.echo("Top Senders:")
    for s in top:
        resp = f"{s.response_rate:.0%}" if s.received_count > 0 else "n/a"
        pattern = ""
        if s.deleted_count > s.replied_count:
            pattern = "→delete"
        elif s.archived_count > s.replied_count:
            pattern = "→archive"
        elif s.replied_count > 0:
            pattern = "→reply"

        typer.echo(
            f"  {s.sender[:30]:30} | recv:{s.received_count:3} resp:{resp:4} "
            f"pri:{s.priority_score:.2f} {pattern}"
        )


@app.command()
def audit_log(limit: int = 20) -> None:
    """Show recent audit log"""
    from life.comms import audit

    logs = audit.get_recent_logs(limit)
    for log_entry in logs:
        typer.echo(
            f"{log_entry['timestamp']} | {log_entry['action']} | "
            f"{log_entry['entity_type']}:{log_entry['entity_id'][:8]}"
        )


@app.command()
def digest(days: int = typer.Option(7, "--days", "-d", help="Number of days to summarize")) -> None:
    """Weekly activity digest"""
    from life.comms import digest as digest_module

    stats = digest_module.get_digest(days=days)
    typer.echo(digest_module.format_digest(stats))


@app.command()
def triage(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of items to triage"),
    confidence: float = typer.Option(0.7, "--confidence", "-c", help="Minimum confidence"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Show proposals without creating"),
    auto_execute: bool = typer.Option(False, "--execute", "-x", help="Auto-execute after approval"),
) -> None:
    """Triage inbox — Claude bulk-proposes actions"""
    from life.comms import triage as triage_module

    typer.echo("Scanning inbox...")
    triage_proposals = triage_module.triage_inbox(limit=limit)

    if not triage_proposals:
        typer.echo("No items to triage or triage failed")
        return

    typer.echo(f"\nFound {len(triage_proposals)} proposals:\n")

    for p in triage_proposals:
        conf = f"{p.confidence:.0%}"
        source = "📧" if p.item.source == "email" else "💬"
        skip = " (skip)" if p.confidence < confidence or p.action == "ignore" else ""
        typer.echo(f"{source} [{conf}] {p.action:10} {p.item.sender[:20]:20} {p.reasoning}{skip}")

    created = triage_module.create_proposals_from_triage(
        triage_proposals,
        min_confidence=confidence,
        dry_run=dry_run,
    )

    if dry_run:
        typer.echo(f"\nDry run: would create {len(created)} proposals")
        return

    typer.echo(f"\nCreated {len(created)} proposals")

    if auto_execute and created:
        typer.echo("\nExecuting approved proposals...")
        results = services.execute_approved_proposals()
        executed = sum(1 for r in results if r.success)
        typer.echo(f"Executed: {executed}/{len(results)}")


@app.command()
def clear(
    limit: int = typer.Option(50, "--limit", "-n", help="Max items to process"),
    confidence: float = typer.Option(0.8, "--confidence", "-c", help="Auto-approve threshold"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Show what would happen"),
) -> None:
    """One-command inbox clear: triage → approve → execute"""
    from life.comms import proposals as proposals_module
    from life.comms import triage as triage_module

    typer.echo("Scanning inbox...")
    triage_proposals = triage_module.triage_inbox(limit=limit)

    if not triage_proposals:
        typer.echo("Inbox clear — nothing to triage")
        return

    from life.comms.contacts import get_high_priority_patterns

    high_priority = get_high_priority_patterns()

    def _is_high_priority(p: Any) -> bool:
        sender_lower = p.item.sender.lower()
        return any(pat in sender_lower for pat in high_priority)

    auto_items = [
        p
        for p in triage_proposals
        if p.confidence >= confidence and p.action != "ignore" and not _is_high_priority(p)
    ]
    review_items = [
        p
        for p in triage_proposals
        if p.confidence < confidence or p.action == "ignore" or _is_high_priority(p)
    ]

    typer.echo(f"\nAuto ({len(auto_items)}) | Review ({len(review_items)})\n")

    for p in auto_items:
        source = "📧" if p.item.source == "email" else "💬"
        typer.echo(f"  {source} {p.action:8} {p.item.sender[:25]:25} {p.reasoning[:30]}")

    if review_items:
        typer.echo("\nNeeds review:")
        for p in review_items:
            source = "📧" if p.item.source == "email" else "💬"
            typer.echo(
                f"  {source} [{p.confidence:.0%}] {p.item.sender[:25]:25} {p.item.preview[:30]}"
            )

    if dry_run:
        typer.echo(f"\nDry run: would auto-execute {len(auto_items)} items")
        return

    created = triage_module.create_proposals_from_triage(
        auto_items, min_confidence=0.0, dry_run=False
    )

    for pid, _ in created:
        proposals_module.approve_proposal(pid)

    results = services.execute_approved_proposals()
    executed = sum(1 for r in results if r.success)

    typer.echo(f"\nExecuted: {executed}/{len(results)}")
    if review_items:
        typer.echo(f"Run `comms review` for {len(review_items)} items needing attention")
