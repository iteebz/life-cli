import os
from pathlib import Path

from ..errors import exit_error

_DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/anthropic"
_DEFAULT_ENV_FILE = Path.home() / "life" / ".env"


def _read_env_file_value(path: Path, key: str) -> str | None:
    if not path.exists():
        return None
    prefix = f"{key}="
    for line in path.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("#") or not s.startswith(prefix):
            continue
        value = s[len(prefix) :].strip().strip('"').strip("'")
        if value:
            return value
    return None


def build_env() -> dict[str, str]:
    env = os.environ.copy()
    zai_key = env.get("ZAI_API_KEY") or _read_env_file_value(_DEFAULT_ENV_FILE, "ZAI_API_KEY")
    if not zai_key:
        exit_error(
            f"ZAI_API_KEY is not set and was not found in {_DEFAULT_ENV_FILE}"
        )

    env["ANTHROPIC_AUTH_TOKEN"] = zai_key
    env["ANTHROPIC_BASE_URL"] = env.get("ANTHROPIC_BASE_URL", _DEFAULT_BASE_URL)
    env["API_TIMEOUT_MS"] = env.get("API_TIMEOUT_MS", "3000000")
    env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = env.get(
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "1"
    )
    env.pop("ANTHROPIC_DEFAULT_OPUS_MODEL", None)
    env.pop("ANTHROPIC_DEFAULT_SONNET_MODEL", None)
    return env


def build_command(prompt: str) -> list[str]:
    return [
        "claude",
        "--print",
        "--verbose",
        "--output-format",
        "stream-json",
        "--dangerously-skip-permissions",
        prompt,
    ]
