"""Merge two encrypted vault files, with conflict resolution."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import decrypt_file, encrypt_file


@dataclass
class MergeResult:
    merged: Dict[str, str]
    conflicts: List[str] = field(default_factory=list)
    added: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)


def _parse_env(text: str) -> Dict[str, str]:
    """Parse decrypted env text into a key→value dict."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        result[key.strip()] = value.strip()
    return result


def _dict_to_env(data: Dict[str, str]) -> str:
    """Serialise a key→value dict back to .env text."""
    return "\n".join(f"{k}={v}" for k, v in sorted(data.items())) + "\n"


def merge_vaults(
    base_path: Path,
    other_path: Path,
    base_password: str,
    other_password: str,
    output_path: Path,
    out_password: str,
    strategy: str = "ours",
) -> MergeResult:
    """Merge *other* vault into *base* vault.

    strategy:
        'ours'   – keep base value on conflict  (default)
        'theirs' – keep other value on conflict
    """
    if strategy not in ("ours", "theirs"):
        raise ValueError(f"Unknown merge strategy: {strategy!r}")

    base_text = decrypt_file(base_path, base_password)
    other_text = decrypt_file(other_path, other_password)

    base_env = _parse_env(base_text)
    other_env = _parse_env(other_text)

    merged: Dict[str, str] = dict(base_env)
    conflicts: List[str] = []
    added: List[str] = []
    overwritten: List[str] = []

    for key, value in other_env.items():
        if key not in merged:
            merged[key] = value
            added.append(key)
        elif merged[key] != value:
            conflicts.append(key)
            if strategy == "theirs":
                merged[key] = value
                overwritten.append(key)

    merged_text = _dict_to_env(merged)
    encrypt_file(merged_text, output_path, out_password)

    return MergeResult(
        merged=merged,
        conflicts=conflicts,
        added=added,
        overwritten=overwritten,
    )
