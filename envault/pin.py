"""Pin management: lock a vault to a specific snapshot by label or ID."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from envault.snapshot import _snapshot_dir, list_snapshots, restore_snapshot


def _pin_path(vault_path: Path) -> Path:
    """Return the path to the pin file for a given vault."""
    return vault_path.parent / (vault_path.name + ".pin")


def set_pin(vault_path: Path, snapshot_id: str) -> dict:
    """Pin a vault to a specific snapshot ID.

    Raises ValueError if the snapshot does not exist.
    Returns the pin record written to disk.
    """
    vault_path = Path(vault_path)
    snapshots = list_snapshots(vault_path)
    ids = [s["id"] for s in snapshots]
    if snapshot_id not in ids:
        raise ValueError(f"Snapshot '{snapshot_id}' not found for vault '{vault_path}'.")

    pin = {"vault": str(vault_path), "pinned_to": snapshot_id}
    pin_file = _pin_path(vault_path)
    pin_file.write_text(json.dumps(pin, indent=2))
    return pin


def get_pin(vault_path: Path) -> Optional[dict]:
    """Return the current pin record for a vault, or None if unpinned."""
    pin_file = _pin_path(Path(vault_path))
    if not pin_file.exists():
        return None
    return json.loads(pin_file.read_text())


def clear_pin(vault_path: Path) -> bool:
    """Remove the pin for a vault. Returns True if a pin existed."""
    pin_file = _pin_path(Path(vault_path))
    if pin_file.exists():
        pin_file.unlink()
        return True
    return False


def restore_pinned(vault_path: Path, password: str) -> Optional[str]:
    """Restore the vault to its pinned snapshot, if any.

    Returns the snapshot ID that was restored, or None if unpinned.
    """
    pin = get_pin(vault_path)
    if pin is None:
        return None
    snapshot_id = pin["pinned_to"]
    restore_snapshot(vault_path, snapshot_id, password)
    return snapshot_id
