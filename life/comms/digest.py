"""Weekly digest — summary of communication activity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from . import db


@dataclass
class DigestStats:
    period_start: datetime
    period_end: datetime
    drafts_created: int
    drafts_sent: int
    proposals_approved: int
    proposals_rejected: int
    proposals_executed: int
    threads_archived: int
    threads_deleted: int
    threads_flagged: int
    top_senders: list[tuple[str, int]]
    pending_drafts: int
    pending_proposals: int


def get_digest(days: int = 7) -> DigestStats:
    end = datetime.now()
    start = end - timedelta(days=days)
    start_iso = start.isoformat()

    with db.get_db() as conn:
        drafts_created = conn.execute(
            "SELECT COUNT(*) FROM drafts WHERE created_at >= ?", (start_iso,)
        ).fetchone()[0]

        drafts_sent = conn.execute(
            "SELECT COUNT(*) FROM drafts WHERE sent_at >= ?", (start_iso,)
        ).fetchone()[0]

        proposals_approved = conn.execute(
            "SELECT COUNT(*) FROM proposals WHERE approved_at >= ? AND status = 'approved'",
            (start_iso,),
        ).fetchone()[0]

        proposals_rejected = conn.execute(
            "SELECT COUNT(*) FROM proposals WHERE rejected_at >= ?",
            (start_iso,),
        ).fetchone()[0]

        proposals_executed = conn.execute(
            "SELECT COUNT(*) FROM proposals WHERE executed_at >= ?", (start_iso,)
        ).fetchone()[0]

        audit_rows = conn.execute(
            "SELECT action, COUNT(*) as cnt FROM audit_log WHERE timestamp >= ? GROUP BY action",
            (start_iso,),
        ).fetchall()

        action_counts = {row["action"]: row["cnt"] for row in audit_rows}

        sender_rows = conn.execute(
            """SELECT sender, received_count FROM sender_stats
            ORDER BY received_count DESC LIMIT 5""",
        ).fetchall()

        top_senders = [(row["sender"], row["received_count"]) for row in sender_rows]

        pending_drafts = conn.execute(
            "SELECT COUNT(*) FROM drafts WHERE sent_at IS NULL AND approved_at IS NULL"
        ).fetchone()[0]

        pending_proposals = conn.execute(
            "SELECT COUNT(*) FROM proposals WHERE status = 'pending'"
        ).fetchone()[0]

    return DigestStats(
        period_start=start,
        period_end=end,
        drafts_created=drafts_created,
        drafts_sent=drafts_sent,
        proposals_approved=proposals_approved,
        proposals_rejected=proposals_rejected,
        proposals_executed=proposals_executed,
        threads_archived=action_counts.get("archive", 0),
        threads_deleted=action_counts.get("delete", 0),
        threads_flagged=action_counts.get("flag", 0),
        top_senders=top_senders,
        pending_drafts=pending_drafts,
        pending_proposals=pending_proposals,
    )


def format_digest(stats: DigestStats) -> str:
    lines = [
        f"Digest: {stats.period_start.strftime('%m/%d')} - {stats.period_end.strftime('%m/%d')}",
        "",
        "Activity:",
        f"  Drafts: {stats.drafts_created} created, {stats.drafts_sent} sent",
        f"  Proposals: {stats.proposals_approved} approved, {stats.proposals_rejected} rejected",
        f"  Executed: {stats.proposals_executed}",
        f"  Threads: {stats.threads_archived} archived, {stats.threads_deleted} deleted, {stats.threads_flagged} flagged",
    ]

    if stats.top_senders:
        lines.append("")
        lines.append("Top senders (all time):")
        for sender, count in stats.top_senders:
            lines.append(f"  {sender[:30]:30} ({count})")

    if stats.pending_drafts or stats.pending_proposals:
        lines.append("")
        lines.append("Pending:")
        if stats.pending_drafts:
            lines.append(f"  {stats.pending_drafts} drafts awaiting approval")
        if stats.pending_proposals:
            lines.append(f"  {stats.pending_proposals} proposals awaiting review")

    return "\n".join(lines)
