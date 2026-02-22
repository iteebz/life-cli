import subprocess
import sys
from pathlib import Path
from typing import Any

PLIST_NAME = "com.comms-cli.daemon.plist"
LAUNCHD_DIR = Path.home() / "Library/LaunchAgents"
PLIST_PATH = LAUNCHD_DIR / PLIST_NAME


def _get_python_path() -> str:
    return sys.executable


def _get_comms_path() -> str:
    result = subprocess.run(["which", "comms"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return str(Path(sys.executable).parent / "comms")


def _generate_plist(interval: int = 5) -> str:
    python_path = _get_python_path()
    comms_path = _get_comms_path()

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.comms-cli.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>{comms_path}</string>
        <string>daemon-start</string>
        <string>--foreground</string>
        <string>--interval</string>
        <string>{interval}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{Path.home()}/.comms/daemon.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>{Path.home()}/.comms/daemon.stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>{Path(python_path).parent}:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
"""


def install(interval: int = 5) -> tuple[bool, str]:
    LAUNCHD_DIR.mkdir(parents=True, exist_ok=True)

    plist_content = _generate_plist(interval)
    PLIST_PATH.write_text(plist_content)

    result = subprocess.run(
        ["launchctl", "load", str(PLIST_PATH)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return False, result.stderr or "Failed to load plist"

    return True, f"Installed and loaded {PLIST_PATH}"


def uninstall() -> tuple[bool, str]:
    if not PLIST_PATH.exists():
        return False, "Not installed"

    subprocess.run(
        ["launchctl", "unload", str(PLIST_PATH)],
        capture_output=True,
        text=True,
    )

    PLIST_PATH.unlink(missing_ok=True)
    return True, "Uninstalled"


def status() -> dict[str, Any]:
    installed = PLIST_PATH.exists()

    running = False
    if installed:
        result = subprocess.run(
            ["launchctl", "list", "com.comms-cli.daemon"],
            capture_output=True,
            text=True,
        )
        running = result.returncode == 0

    return {
        "installed": installed,
        "running": running,
        "plist_path": str(PLIST_PATH) if installed else None,
    }
