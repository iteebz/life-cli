import json


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

    def parse_line(self, line: str) -> dict[str, object] | None:
        raw = line.strip()
        if not raw:
            return None
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            return {"type": "raw", "raw": raw}
        if not isinstance(event, dict):
            return {"type": "raw", "raw": raw}

        event_type = event.get("type")

        if event_type in {"system", "context_init"}:
            session_id = event.get("session_id") or event.get("sessionId") or ""
            model = event.get("model") or ""
            return {"type": "system", "session_id": session_id, "model": model}

        if event_type == "assistant":
            return self._parse_assistant(event)

        if event_type == "user":
            return self._parse_user(event)

        if event_type == "error" or (event_type == "result" and event.get("subtype") == "error"):
            message = event.get("error") or event.get("message") or event.get("result") or "unknown error"
            if isinstance(message, dict):
                message = message.get("message") or message.get("error") or str(message)
            return {"type": "error", "message": _short(message, 240)}

        return {"type": "raw", "raw": raw}

    def _parse_assistant(self, event: dict[str, object]) -> dict[str, object] | None:
        msg = event.get("message")
        if not isinstance(msg, dict):
            return {"type": "raw", "raw": json.dumps(event, ensure_ascii=True)}

        usage = msg.get("usage")
        if isinstance(usage, dict):
            return {
                "type": "usage",
                "input_tokens": int(usage.get("input_tokens", 0)),
                "output_tokens": int(usage.get("output_tokens", 0)),
                "cache_tokens": int(usage.get("cache_read_input_tokens", 0))
                + int(usage.get("cache_creation_input_tokens", 0)),
            }

        blocks = msg.get("content")
        if not isinstance(blocks, list):
            return None

        for block in blocks:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "text":
                text = block.get("text")
                if isinstance(text, str) and text.strip():
                    return {"type": "assistant_text", "text": text.strip()}
            if block_type == "tool_use":
                tool_use_id = str(block.get("id", ""))
                tool_name = str(block.get("name", ""))
                if tool_use_id and tool_name:
                    self._tool_map[tool_use_id] = tool_name
                return {
                    "type": "tool_call",
                    "tool_use_id": tool_use_id,
                    "tool_name": tool_name,
                    "args": block.get("input", {}),
                }
        return None

    def _parse_user(self, event: dict[str, object]) -> dict[str, object] | None:
        msg = event.get("message")
        if not isinstance(msg, dict):
            return None
        content = msg.get("content")
        if not isinstance(content, list):
            return None
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_result":
                continue
            tool_use_id = str(block.get("tool_use_id", ""))
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "tool_name": block.get("tool_name") or self._tool_map.get(tool_use_id, ""),
                "result": _stringify_content(block.get("content", "")),
                "is_error": bool(block.get("is_error")),
            }
        return None


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
