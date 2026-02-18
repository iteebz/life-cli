import json

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
        return f"tool: {tool_name}({_short(entry.get('args', {}), 140)})"
    if kind == "tool_result":
        tool_name = entry.get("tool_name") or "unknown"
        prefix = "error" if entry.get("is_error") else "result"
        return f"{prefix}: {tool_name} {_short(entry.get('result', ''), 220)}"
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
