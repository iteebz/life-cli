"""Reply templates — common responses Claude can use."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

TEMPLATES_PATH = Path.home() / ".comms" / "templates.md"

DEFAULT_TEMPLATES = """## ack
Thanks for sending this over. I'll review and get back to you.

## busy
Thanks for reaching out. I'm swamped right now but will circle back when I have bandwidth.

## decline
Thanks for thinking of me, but I'll have to pass on this one.

## delegate
Looping in [NAME] who can help with this.

## meeting
Works for me. Send over a calendar invite.

## later
Can we revisit this next week? I want to give it proper attention.

## received
Got it, thanks.

## followup
Just following up on this — any updates?
"""


@dataclass
class Template:
    name: str
    body: str


def _load_templates() -> list[Template]:
    if not TEMPLATES_PATH.exists():
        return _parse_templates(DEFAULT_TEMPLATES)

    return _parse_templates(TEMPLATES_PATH.read_text())


def _parse_templates(content: str) -> list[Template]:
    templates = []
    current_name = None
    current_lines: list[str] = []

    for line in content.splitlines():
        if line.startswith("## "):
            if current_name:
                templates.append(Template(name=current_name, body="\n".join(current_lines).strip()))
            current_name = line[3:].strip()
            current_lines = []
        elif current_name:
            current_lines.append(line)

    if current_name:
        templates.append(Template(name=current_name, body="\n".join(current_lines).strip()))

    return templates


def get_templates() -> list[Template]:
    return _load_templates()


def get_template(name: str) -> Template | None:
    templates = _load_templates()
    for t in templates:
        if t.name.lower() == name.lower():
            return t
    return None


def format_templates_for_prompt() -> str:
    templates = _load_templates()
    if not templates:
        return ""

    lines = ["QUICK REPLY TEMPLATES (use if appropriate, customize as needed):"]
    for t in templates:
        preview = t.body[:50].replace("\n", " ")
        lines.append(f"- {t.name}: {preview}...")

    return "\n".join(lines)


def init_templates():
    if not TEMPLATES_PATH.exists():
        TEMPLATES_PATH.parent.mkdir(parents=True, exist_ok=True)
        TEMPLATES_PATH.write_text(DEFAULT_TEMPLATES)
