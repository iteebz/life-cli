import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

SIGNAL_CLI = "signal-cli"
PEOPLE_DIR = Path.home() / "life" / "steward" / "people"


def _default_account() -> str | None:
    result = subprocess.run(
        [SIGNAL_CLI, "listAccounts"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return None
    for line in result.stdout.strip().split("\n"):
        if line.startswith("Number: "):
            return line.replace("Number: ", "").strip()
    return None


def resolve_contact(name_or_number: str) -> str:
    if name_or_number.startswith("+") or name_or_number.lstrip("0").isdigit():
        return name_or_number

    if not PEOPLE_DIR.exists():
        return name_or_number

    name_lower = name_or_number.lower()
    for profile in PEOPLE_DIR.glob("*.md"):
        text = profile.read_text()
        match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        if not match:
            continue
        try:
            frontmatter = yaml.safe_load(match.group(1))
        except Exception:  # noqa: S112
            continue
        if not isinstance(frontmatter, dict):
            continue
        signal_num = frontmatter.get("signal")
        if not signal_num:
            continue
        if profile.stem.lower() == name_lower:
            return str(signal_num)
        name_field = frontmatter.get("name", "")
        if isinstance(name_field, str) and name_field.lower() == name_lower:
            return str(signal_num)

    return name_or_number


def send(recipient: str, message: str, attachment: str | None = None) -> tuple[bool, str]:
    phone = _default_account()
    if not phone:
        return False, "no Signal account registered with signal-cli"

    cmd = [SIGNAL_CLI, "-a", phone, "send"]
    if attachment:
        cmd.extend(["--attachment", attachment])
    cmd.extend(["-m", message, recipient])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        return True, "sent"
    return False, result.stderr.strip() or "send failed"


def receive(timeout: int = 5) -> list[dict[str, Any]]:
    phone = _default_account()
    if not phone:
        return []

    result = subprocess.run(
        [SIGNAL_CLI, "-a", phone, "receive", "-t", str(timeout)],
        capture_output=True,
        text=True,
        timeout=timeout + 10,
    )
    if result.returncode != 0:
        return []

    messages = []
    output = result.stdout + result.stderr

    envelope_pattern = re.compile(r'Envelope from: "([^"]*)" (\+\d+)', re.MULTILINE)
    body_pattern = re.compile(r"^Body: (.+)$", re.MULTILINE)
    timestamp_pattern = re.compile(r"^Timestamp: (\d+)", re.MULTILINE)

    blocks = re.split(r"\n(?=Envelope from:)", output)
    for block in blocks:
        envelope_match = envelope_pattern.search(block)
        body_match = body_pattern.search(block)
        timestamp_match = timestamp_pattern.search(block)
        if envelope_match and body_match:
            messages.append(
                {
                    "from": envelope_match.group(2),
                    "from_name": envelope_match.group(1),
                    "body": body_match.group(1),
                    "timestamp": int(timestamp_match.group(1)) if timestamp_match else 0,
                }
            )

    return messages


def list_accounts() -> list[str]:
    result = subprocess.run(
        [SIGNAL_CLI, "listAccounts"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return []
    return [
        line.replace("Number: ", "").strip()
        for line in result.stdout.strip().split("\n")
        if line.startswith("Number: ")
    ]


def _run(args: list[str], account: str) -> dict[str, Any] | list[Any] | None:
    cmd = [SIGNAL_CLI, "-a", account, *args, "--output=json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None
        if not result.stdout.strip():
            return {}
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def list_contacts() -> list[dict[str, Any]]:
    phone = _default_account()
    if not phone:
        return []
    result = _run(["listContacts"], phone)
    if not result or not isinstance(result, list):
        return []
    return [
        {"number": c.get("number", ""), "name": c.get("name", "")}
        for c in result
        if c.get("number")
    ]
