"""Track and display access history for vault files."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

from envault.audit import log_event, read_log


@dataclass
class HistoryEntry:
    timestamp: str
    action: str
    vault: str
    user: str
    note: Optional[str] = None


def record_access(vault_path: str | Path, action: str, user: Optional[str] = None, note: Optional[str] = None) -> HistoryEntry:
    """Record a vault access event and return the entry."""
    vault_path = Path(vault_path)
    extra = {"vault": str(vault_path), "note": note}
    event = log_event(action, user=user, extra=extra)
    return HistoryEntry(
        timestamp=event["timestamp"],
        action=event["action"],
        vault=str(vault_path),
        user=event["user"],
        note=note,
    )


def get_vault_history(vault_path: str | Path, limit: Optional[int] = None) -> List[HistoryEntry]:
    """Return history entries for a specific vault file."""
    vault_str = str(Path(vault_path))
    all_events = read_log()
    entries: List[HistoryEntry] = []
    for event in all_events:
        extra = event.get("extra") or {}
        if extra.get("vault") == vault_str:
            entries.append(
                HistoryEntry(
                    timestamp=event["timestamp"],
                    action=event["action"],
                    vault=vault_str,
                    user=event["user"],
                    note=extra.get("note"),
                )
            )
    if limit is not None:
        entries = entries[-limit:]
    return entries


def format_history(entries: List[HistoryEntry], fmt: str = "plain") -> str:
    """Format history entries as plain text or JSON."""
    if fmt == "json":
        return json.dumps([asdict(e) for e in entries], indent=2)
    lines = []
    for e in entries:
        note_part = f" [{e.note}]" if e.note else ""
        lines.append(f"{e.timestamp}  {e.action:<20} {e.user}{note_part}")
    return "\n".join(lines) if lines else "(no history)"
