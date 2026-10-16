"""Claude Code PostToolUse hook: run `ruff format` on a Python file that was just edited.

Reads the hook JSON from stdin. Never fails the tool call: if anything is missing
(ruff not installed, no file path, not a .py file) it quietly does nothing.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def find_ruff() -> list[str] | None:
    on_path = shutil.which("ruff")
    if on_path:
        return [on_path]
    for candidate in (ROOT / ".venv" / "Scripts" / "ruff.exe", ROOT / ".venv" / "bin" / "ruff"):
        if candidate.exists():
            return [str(candidate)]
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        file_path = payload.get("tool_input", {}).get("file_path", "")
    except (json.JSONDecodeError, AttributeError):
        return 0

    if not file_path.endswith(".py"):
        return 0

    ruff = find_ruff()
    if ruff is None:
        return 0

    subprocess.run([*ruff, "format", file_path], check=False, capture_output=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
