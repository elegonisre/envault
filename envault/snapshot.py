"""Snapshot management: save and restore named vault snapshots."""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

from envault.audit import log_event

_SNAPSHOT_DIR_NAME = ".envault_snapshots"


@dataclass
class SnapshotMeta:
    name: str
    vault_path: str
    created_at: str
    note: str = ""


def _snapshot_dir(vault_path: Path) -> Path:
    return vault_path.parent / _SNAPSHOT_DIR_NAME


def _meta_path(vault_path: Path, name: str) -> Path:
    return _snapshot_dir(vault_path) / f"{name}.meta.json"


def _snap_path(vault_path: Path, name: str) -> Path:
    return _snapshot_dir(vault_path) / f"{name}.vault"


def save_snapshot(
    vault_path: Path,
    name: str,
    note: str = "",
    user: Optional[str] = None,
) -> SnapshotMeta:
    """Copy *vault_path* into the snapshot store under *name*."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault not found: {vault_path}")
    sdir = _snapshot_dir(vault_path)
    sdir.mkdir(parents=True, exist_ok=True)

    from envault.audit import _utc_now
    meta = SnapshotMeta(
        name=name,
        vault_path=str(vault_path.resolve()),
        created_at=_utc_now(),
        note=note,
    )
    shutil.copy2(vault_path, _snap_path(vault_path, name))
    _meta_path(vault_path, name).write_text(json.dumps(asdict(meta), indent=2))
    log_event("snapshot_save", vault=str(vault_path), snapshot=name, user=user)
    return meta


def restore_snapshot(
    vault_path: Path,
    name: str,
    user: Optional[str] = None,
) -> Path:
    """Overwrite *vault_path* with the named snapshot. Returns vault_path."""
    vault_path = Path(vault_path)
    src = _snap_path(vault_path, name)
    if not src.exists():
        raise FileNotFoundError(f"Snapshot '{name}' not found for {vault_path}")
    shutil.copy2(src, vault_path)
    log_event("snapshot_restore", vault=str(vault_path), snapshot=name, user=user)
    return vault_path


def list_snapshots(vault_path: Path) -> List[SnapshotMeta]:
    """Return all snapshots for *vault_path*, sorted by creation time."""
    sdir = _snapshot_dir(Path(vault_path))
    if not sdir.exists():
        return []
    metas = []
    for meta_file in sorted(sdir.glob("*.meta.json")):
        data = json.loads(meta_file.read_text())
        metas.append(SnapshotMeta(**data))
    return sorted(metas, key=lambda m: m.created_at)


def delete_snapshot(vault_path: Path, name: str, user: Optional[str] = None) -> None:
    """Remove a named snapshot from the store."""
    vault_path = Path(vault_path)
    for p in (_snap_path(vault_path, name), _meta_path(vault_path, name)):
        if p.exists():
            p.unlink()
    log_event("snapshot_delete", vault=str(vault_path), snapshot=name, user=user)
