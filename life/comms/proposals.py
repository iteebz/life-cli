import uuid
from typing import Any

from . import accounts as accts_module
from . import audit, drafts, learning
from .adapters.email import gmail
from .adapters.messaging import signal
from .db import get_db, now_iso

VALID_ACTIONS = {
    "thread": {"archive", "delete", "flag", "unflag", "unarchive", "undelete"},
    "draft": {"approve", "send", "delete"},
    "signal_message": {"mark_read", "ignore"},
}


def _validate_entity(entity_type: str, entity_id: str, email: str | None) -> tuple[bool, str]:
    def validate_thread() -> bool:
        acc = accts_module.select_email_account(email)[0]
        if not acc:
            return False
        acc_email = acc.get("email") or email or ""
        return bool(gmail.fetch_thread_messages(entity_id, acc_email))

    validators = {
        "thread": validate_thread,
        "draft": lambda: drafts.get_draft(entity_id),
        "signal_message": lambda: signal.get_message(entity_id),
    }
    if entity_type not in validators:
        return False, f"Unknown entity_type: {entity_type}"
    try:
        return (bool(validators[entity_type]()), "")
    except Exception as e:
        return False, f"Failed to validate {entity_type}: {e}"


def _validate_action(entity_type: str, proposed_action: str) -> tuple[bool, str]:
    if entity_type not in VALID_ACTIONS:
        return False, f"Unknown entity_type: {entity_type}"
    if proposed_action not in VALID_ACTIONS[entity_type]:
        return (
            False,
            f"Invalid action '{proposed_action}' for {entity_type}. Valid: {VALID_ACTIONS[entity_type]}",
        )
    return True, ""


def create_proposal(
    entity_type: str,
    entity_id: str,
    proposed_action: str,
    agent_reasoning: str | None = None,
    email: str | None = None,
    skip_validation: bool = False,
) -> tuple[str | None, str, bool]:
    if not skip_validation:
        valid_action, msg = _validate_action(entity_type, proposed_action)
        if not valid_action:
            return None, msg, False

        valid_entity, msg = _validate_entity(entity_type, entity_id, email)
        if not valid_entity:
            return None, msg, False

    auto_approved = learning.should_auto_approve(proposed_action)
    status = "approved" if auto_approved else "pending"

    proposal_id = str(uuid.uuid4())

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO proposals (id, entity_type, entity_id, proposed_action, agent_reasoning, email, proposed_at, status, approved_at, approved_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal_id,
                entity_type,
                entity_id,
                proposed_action,
                agent_reasoning,
                email,
                now_iso(),
                status,
                now_iso() if auto_approved else None,
                "auto" if auto_approved else None,
            ),
        )

    if auto_approved:
        audit.log_decision(
            proposed_action=proposed_action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_decision="auto_approved",
            reasoning="Confidence threshold met",
            metadata={"proposal_id": proposal_id, "agent_reasoning": agent_reasoning},
        )

    return proposal_id, "", auto_approved


def get_proposal(proposal_id: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,)).fetchone()
        if not row:
            return None
        return dict(row)


def list_proposals(status: str | None = None) -> list[dict[str, Any]]:
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM proposals WHERE status = ? ORDER BY proposed_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM proposals ORDER BY proposed_at DESC").fetchall()

        return [dict(row) for row in rows]


def _resolve_proposal_id(proposal_id_prefix: str) -> str | None:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id FROM proposals WHERE id LIKE ? ORDER BY proposed_at DESC",
            (f"{proposal_id_prefix}%",),
        ).fetchall()

        if len(rows) == 1:
            return rows[0]["id"]
        return None


def approve_proposal(proposal_id: str, user_reasoning: str | None = None) -> bool:
    full_id = _resolve_proposal_id(proposal_id) or proposal_id

    with get_db() as conn:
        row = conn.execute("SELECT * FROM proposals WHERE id = ?", (full_id,)).fetchone()
        if not row:
            return False

        proposal = dict(row)
        if proposal["status"] != "pending":
            return False

        conn.execute(
            """
            UPDATE proposals
            SET status = 'approved', approved_at = ?, approved_by = 'user', user_reasoning = ?
            WHERE id = ?
            """,
            (now_iso(), user_reasoning, full_id),
        )

    audit.log_decision(
        proposed_action=proposal["proposed_action"],
        entity_type=proposal["entity_type"],
        entity_id=proposal["entity_id"],
        user_decision="approved",
        reasoning=user_reasoning,
        metadata={"proposal_id": proposal_id, "agent_reasoning": proposal["agent_reasoning"]},
    )

    return True


def reject_proposal(
    proposal_id: str, user_reasoning: str | None = None, correction: str | None = None
) -> bool:
    full_id = _resolve_proposal_id(proposal_id) or proposal_id

    with get_db() as conn:
        row = conn.execute("SELECT * FROM proposals WHERE id = ?", (full_id,)).fetchone()
        if not row:
            return False

        proposal = dict(row)
        if proposal["status"] != "pending":
            return False

        conn.execute(
            """
            UPDATE proposals
            SET status = 'rejected', rejected_at = ?, user_reasoning = ?, correction = ?
            WHERE id = ?
            """,
            (now_iso(), user_reasoning, correction, full_id),
        )

    decision_type = "rejected_with_correction" if correction else "rejected"
    metadata = {
        "proposal_id": proposal_id,
        "agent_reasoning": proposal["agent_reasoning"],
    }
    if correction:
        metadata["correction"] = correction

    audit.log_decision(
        proposed_action=proposal["proposed_action"],
        entity_type=proposal["entity_type"],
        entity_id=proposal["entity_id"],
        user_decision=decision_type,
        reasoning=user_reasoning,
        metadata=metadata,
    )

    return True


def mark_executed(proposal_id: str) -> bool:
    with get_db() as conn:
        conn.execute(
            "UPDATE proposals SET status = 'executed', executed_at = ? WHERE id = ?",
            (now_iso(), proposal_id),
        )

    proposal = get_proposal(proposal_id)
    if proposal:
        audit.log(
            action="execute",
            entity_type=proposal["entity_type"],
            entity_id=proposal["entity_id"],
            metadata={"proposal_id": proposal_id, "action": proposal["proposed_action"]},
        )

    return True


def get_approved_proposals() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM proposals WHERE status = 'approved' ORDER BY approved_at ASC"
        ).fetchall()
        return [dict(row) for row in rows]
