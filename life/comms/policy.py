from datetime import datetime

from .config import get_policy
from .db import get_db


def check_recipient_allowed(recipient: str) -> tuple[bool, str]:
    policy = get_policy()
    allowed_recipients: list[str] = policy.get("allowed_recipients", [])
    allowed_domains: list[str] = policy.get("allowed_domains", [])

    if recipient in allowed_recipients:
        return True, "recipient allowlisted"

    domain = recipient.split("@")[-1] if "@" in recipient else ""
    if domain in allowed_domains:
        return True, "domain allowlisted"

    if not allowed_recipients and not allowed_domains:
        return True, "no restrictions configured"

    return False, f"recipient '{recipient}' not in allowlist"


def check_daily_send_limit() -> tuple[bool, str]:
    policy = get_policy()
    max_daily: int = policy.get("max_daily_sends", 50)

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    with get_db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM drafts WHERE sent_at >= ?", (today_start.isoformat(),)
        ).fetchone()[0]

    if count >= max_daily:
        return False, f"daily send limit reached ({count}/{max_daily})"

    return True, f"within daily limit ({count}/{max_daily})"


def requires_approval() -> bool:
    policy = get_policy()
    return bool(policy.get("require_approval", True))


def validate_send(draft_id: str, to_addr: str) -> tuple[bool, list[str]]:
    errors = []

    allowed, msg = check_recipient_allowed(to_addr)
    if not allowed:
        errors.append(msg)

    within_limit, msg = check_daily_send_limit()
    if not within_limit:
        errors.append(msg)

    if requires_approval():
        with get_db() as conn:
            draft = conn.execute(
                "SELECT approved_at FROM drafts WHERE id = ?", (draft_id,)
            ).fetchone()
            if not draft or not draft["approved_at"]:
                errors.append("draft requires approval before sending")

    return len(errors) == 0, errors
