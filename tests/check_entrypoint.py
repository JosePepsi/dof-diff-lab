from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "dof_diff_lab", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    for command in ("sync", "build", "search", "discover", "triage"):
        assert command in result.stdout, (command, result.stdout)

    environment = os.environ.copy()
    environment.pop("TAVILY_API_KEY", None)
    failed_discovery = subprocess.run(
        [sys.executable, "-m", "dof_diff_lab", "discover", "trade notices"],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert failed_discovery.returncode == 2
    assert "TAVILY_API_KEY" in failed_discovery.stderr
    assert failed_discovery.stdout == ""


if __name__ == "__main__":
    main()
