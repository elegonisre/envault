"""Audit log for envault operations — tracks encrypt/decrypt/share events."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_AUDIT_FILE = ".envault_audit.log"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _audit_path(audit_file: Optional[str] = None) -> Path:
    return Path(audit_file or DEFAULT_AUDIT_FILE)


def log_event(
    action: str,
    target: str,
    user: Optional[str] = None,
    extra: Optional[dict] = None,
    audit_file: Optional[str] = None,
) -> dict:
    """Append a structured audit entry and return it."""
    entry = {
        "timestamp": _utc_now(),
        "action": action,
        "target": target,
        "user": user or os.environ.get("USER", "unknown"),
        **(extra or {}),
    }
    path = _audit_path(audit_file)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    return entry


def read_log(audit_file: Optional[str] = None) -> list[dict]:
    """Return all audit entries as a list of dicts."""
    path = _audit_path(audit_file)
    if not path.exists():
        return []
    entries = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def clear_log(audit_file: Optional[str] = None) -> None:
    """Remove the audit log file entirely."""
    path = _audit_path(audit_file)
    if path.exists():
        path.unlink()
