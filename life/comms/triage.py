"""Triage automation — Claude bulk-proposes actions for inbox items."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

from . import proposals as proposals_module
from .config import RULES_PATH
from .contacts import format_contacts_for_prompt, get_high_priority_patterns
from .patterns import detect_urgency, should_skip_triage
from .senders import format_sender_context_for_prompt
from .services import InboxItem, get_unified_inbox
from .snooze import get_due_snoozes, is_snoozed, mark_resurfaced


@dataclass
class TriageProposal:
    item: InboxItem
    action: str
    reasoning: str
    confidence: float


def _load_rules() -> str:
    if RULES_PATH.exists():
        return RULES_PATH.read_text()
    return ""


def _build_prompt(items: list[InboxItem], rules: str) -> str:
    items_json = []
    sender_histories = []

    for item in items:
        item_data = {
            "id": item.item_id[:8],
            "source": item.source,
            "sender": item.sender,
            "subject": item.subject,
            "preview": item.preview,
            "unread": item.unread,
        }

        sender_ctx = format_sender_context_for_prompt(item.sender)
        if sender_ctx:
            sender_histories.append(sender_ctx)

        items_json.append(item_data)

    contacts = format_contacts_for_prompt()
    histories = "\n\n".join(sender_histories) if sender_histories else ""

    return f"""You are triaging a communications inbox for someone with ADHD. Analyze each item and propose an action.

STEWARD CONTEXT:
- High-priority contacts (flag always, never auto-archive): people in personal life, close relationships
- High-stakes subjects: legal notices, finance, tax, debt, court — always flag
- Default bias: delete noise aggressively, flag anything requiring a human decision

RULES (user preferences):
{rules or "No rules configured. Use sensible defaults."}

{contacts}

{histories}

VALID ACTIONS:
- For email: archive, delete, flag, ignore
- For signal: mark_read, flag, ignore

OUTPUT FORMAT (JSON array, one object per item):
[
  {{"id": "abc123", "action": "archive", "reasoning": "Newsletter, no response needed", "confidence": 0.9}},
  ...
]

ITEMS TO TRIAGE:
{json.dumps(items_json, indent=2)}

Respond with ONLY the JSON array. No explanation."""


def _parse_response(output: str, items: list[InboxItem]) -> list[TriageProposal]:
    output = output.strip()
    if output.startswith("```"):
        lines = output.split("\n")
        output = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    try:
        proposals_data = json.loads(output)
    except json.JSONDecodeError:
        return []

    item_map = {item.item_id[:8]: item for item in items}
    proposals = []

    for proposal_data in proposals_data:
        item_id = proposal_data.get("id", "")
        if item_id not in item_map:
            continue
        proposals.append(
            TriageProposal(
                item=item_map[item_id],
                action=proposal_data.get("action", "ignore"),
                reasoning=proposal_data.get("reasoning", ""),
                confidence=float(proposal_data.get("confidence", 0.5)),
            )
        )

    return proposals


def _apply_patterns(items: list[InboxItem]) -> tuple[list[TriageProposal], list[InboxItem]]:
    pattern_proposals = []
    remaining = []

    for item in items:
        if item.source != "email":
            remaining.append(item)
            continue

        match = should_skip_triage(item.sender, item.subject, item.preview)
        if match:
            urgency, urgency_reason = detect_urgency(item.subject, item.preview)
            if urgency >= 0.6:
                pattern_proposals.append(
                    TriageProposal(
                        item=item,
                        action="flag",
                        reasoning=f"[auto] {match.reason}, but {urgency_reason}",
                        confidence=urgency,
                    )
                )
            else:
                pattern_proposals.append(
                    TriageProposal(
                        item=item,
                        action=match.action,
                        reasoning=f"[auto] {match.reason}",
                        confidence=match.confidence,
                    )
                )
        else:
            remaining.append(item)

    return pattern_proposals, remaining


def triage_inbox(
    limit: int = 20,
    model: str = "claude-sonnet-4-20250514",
) -> list[TriageProposal]:
    items = get_unified_inbox(limit=limit)
    if not items:
        return []

    due_snoozes = get_due_snoozes()
    for snooze in due_snoozes:
        mark_resurfaced(snooze["id"])

    entity_type_map = {"email": "thread", "signal": "signal_message"}
    items = [
        item
        for item in items
        if not is_snoozed(entity_type_map.get(item.source, "thread"), item.item_id)
    ]

    if not items:
        return []

    pattern_proposals, remaining = _apply_patterns(items)

    if not remaining:
        return pattern_proposals

    rules = _load_rules()
    prompt = _build_prompt(remaining, rules)

    result = subprocess.run(
        [
            "claude",
            "--print",
            "--model",
            model,
            "-p",
            prompt,
            "--dangerously-skip-permissions",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        return pattern_proposals

    claude_proposals = _parse_response(result.stdout, remaining)
    high_priority = get_high_priority_patterns()

    for p in claude_proposals:
        urgency, urgency_reason = detect_urgency(p.item.subject, p.item.preview)
        if urgency >= 0.6 and p.action not in ("flag", "delete"):
            p.reasoning += f" [urgent: {urgency_reason}]"

        sender_lower = p.item.sender.lower()
        if any(pat in sender_lower for pat in high_priority) and p.action not in ("flag",):
            p.action = "flag"
            p.reasoning = f"[steward] high-priority contact — {p.reasoning}"
            p.confidence = 1.0

    return pattern_proposals + claude_proposals


def create_proposals_from_triage(
    proposals: list[TriageProposal],
    min_confidence: float = 0.7,
    dry_run: bool = False,
) -> list[tuple[str, TriageProposal]]:
    created = []
    for p in proposals:
        if p.confidence < min_confidence:
            continue
        if p.action == "ignore":
            continue

        entity_type = "thread" if p.item.source == "email" else "signal_message"

        if dry_run:
            created.append(("dry-run", p))
            continue

        proposal_id, _, _ = proposals_module.create_proposal(
            entity_type=entity_type,
            entity_id=p.item.item_id,
            proposed_action=p.action,
            agent_reasoning=p.reasoning,
            email=p.item.source_id if p.item.source == "email" else None,
            skip_validation=True,
        )

        if proposal_id:
            created.append((proposal_id, p))

    return created
