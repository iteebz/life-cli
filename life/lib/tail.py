import json
import re

from .providers import glm


def _short(value: object, limit: int = 120) -> str:
    text = str(value).strip().replace("\r", "")
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _stringify_content(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text)
                else:
                    parts.append(json.dumps(item, ensure_ascii=True, separators=(",", ":")))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    return str(value)


def _summarize_tool_args(tool_name: str, args: object) -> str:
    if not isinstance(args, dict):
        return _short(args, 140)
    key_order = {
        "Read": ["file_path", "offset", "limit"],
        "Edit": ["file_path", "old_string", "new_string", "replace_all"],
        "Write": ["file_path"],
        "Bash": ["command", "description"],
        "Grep": ["pattern", "path"],
        "Glob": ["pattern", "path"],
        "LS": ["path"],
    }.get(tool_name, ["file_path", "path", "command", "pattern"])
    parts: list[str] = []
    for key in key_order:
        if key not in args:
            continue
        value = args.get(key)
        if key in {"old_string", "new_string"}:
            parts.append(f"{key}={_short(value, 36)}")
        elif key == "command":
            parts.append(f"cmd={_short(value, 80)}")
        else:
            parts.append(f"{key}={_short(value, 48)}")
    if not parts:
        items = list(args.items())[:3]
        parts = [f"{k}={_short(v, 40)}" for k, v in items]
    return ", ".join(parts)


def _summarize_diff(text: str) -> str | None:
    if "diff --git " not in text and "\n--- " not in text and "\n+++ " not in text:
        return None
    files: list[str] = []
    plus = 0
    minus = 0
    for line in text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3]
                if path.startswith("b/"):
                    path = path[2:]
                files.append(path)
            continue
        if line.startswith("+++ ") or line.startswith("--- ") or line.startswith("@@"):
            continue
        if line.startswith("+"):
            plus += 1
        elif line.startswith("-"):
            minus += 1
    files_unique = list(dict.fromkeys(files))
    names = ", ".join(files_unique[:2])
    if len(files_unique) > 2:
        names += ", ..."
    return f"diff: files={len(files_unique) or 1} +{plus} -{minus} {names}".strip()


class StreamParser:
    def __init__(self) -> None:
        self._tool_map: dict[str, str] = {}

    def parse_line(self, line: str) -> list[dict[str, object]]:
        raw = line.strip()
        if not raw:
            return []
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            return [{"type": "raw", "raw": raw}]
        if not isinstance(event, dict):
            return [{"type": "raw", "raw": raw}]
        normalized = glm.normalize_event(event, tool_map=self._tool_map)
        if normalized:
            return normalized
        return [{"type": "raw", "raw": raw}]


def format_entry(entry: dict[str, object], quiet_system: bool = False) -> str | None:
    kind = str(entry.get("type", ""))
    if kind == "assistant_text":
        return f"ai: {_short(entry.get('text', ''), 500)}"
    if kind == "tool_call":
        tool_name = entry.get("tool_name") or "unknown"
        return f"tool: {tool_name}({_summarize_tool_args(str(tool_name), entry.get('args', {}))})"
    if kind == "tool_result":
        tool_name = entry.get("tool_name") or "unknown"
        prefix = "error" if entry.get("is_error") else "result"
        result_text = _stringify_content(entry.get("result", ""))
        diff_summary = _summarize_diff(result_text)
        if diff_summary:
            return f"{prefix}: {tool_name} {diff_summary}"
        clean = result_text
        clean = re.sub(r"\s*\d+→", "\n", clean)
        clean = " ".join(clean.split())
        return f"{prefix}: {tool_name} {_short(clean, 220)}"
    if kind == "system":
        if quiet_system:
            return None
        session_id = _short(entry.get("session_id", ""), 8)
        model = _short(entry.get("model", ""), 40)
        return f"session: {session_id or '-'} model={model or '-'}"
    if kind == "usage":
        in_tokens = int(entry.get("input_tokens", 0))
        out_tokens = int(entry.get("output_tokens", 0))
        cache_tokens = int(entry.get("cache_tokens", 0))
        if in_tokens == 0 and out_tokens == 0 and cache_tokens == 0:
            return None
        return (
            "usage: "
            f"in={in_tokens} "
            f"out={out_tokens} "
            f"cache={cache_tokens}"
        )
    if kind == "error":
        return f"error: {_short(entry.get('message', ''), 240)}"
    if kind == "raw":
        return f"raw: {entry.get('raw', '')}"
    return None
