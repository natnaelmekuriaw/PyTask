import re
import subprocess
from pathlib import Path


def source_revision() -> tuple[str | None, bool | None]:
    root = Path(__file__).resolve().parents[3]
    try:
        head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=2, check=False,
        )
        revision = head.stdout.strip()
        if head.returncode or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", revision) is None:
            return None, None
        status = subprocess.run(
            ["git", "-C", str(root), "diff", "--quiet", "HEAD"],
            capture_output=True, timeout=2, check=False,
        )
        return revision, status.returncode == 1 if status.returncode in (0, 1) else None
    except (OSError, subprocess.TimeoutExpired):
        return None, None

