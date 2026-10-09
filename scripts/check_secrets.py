"""Fail CI when tracked files contain common credential formats."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


SECRET_PATTERNS = [
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\b(?:sk|rk)-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bre_[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b"),
]

ALLOWED_FILENAMES = {".env.example"}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], check=True, capture_output=True
    )
    return [Path(item) for item in result.stdout.decode().split("\0") if item]


def main() -> int:
    findings: list[str] = []
    for path in tracked_files():
        if path.name in ALLOWED_FILENAMES or not path.is_file():
            continue
        if path.name.startswith(".env") or path.name.startswith("secrets"):
            findings.append(f"tracked secret-like file: {path}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(f"possible secret pattern in: {path}")
                break

    if findings:
        print("Secret scan failed:")
        print("\n".join(f"- {finding}" for finding in findings))
        return 1
    print(f"Secret scan passed: {len(tracked_files())} tracked files checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
