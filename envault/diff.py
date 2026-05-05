"""Diff two vault files by decrypting and comparing their keys."""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from envault.vault import decrypt_file


class DiffResult(NamedTuple):
    added: dict[str, str]      # keys present in new, missing in old
    removed: dict[str, str]    # keys present in old, missing in new
    changed: dict[str, tuple[str, str]]  # key -> (old_value, new_value)
    unchanged: list[str]       # keys with identical values


def _parse_env(text: str) -> dict[str, str]:
    """Parse decrypted .env content into a key/value mapping."""
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def diff_vaults(
    old_path: str | Path,
    new_path: str | Path,
    old_password: str,
    new_password: str | None = None,
) -> DiffResult:
    """Decrypt two vault files and return a structured diff.

    If *new_password* is ``None`` the same password is used for both vaults.
    """
    if new_password is None:
        new_password = old_password

    old_text = decrypt_file(str(old_path), old_password)
    new_text = decrypt_file(str(new_path), new_password)

    old_env = _parse_env(old_text)
    new_env = _parse_env(new_text)

    added: dict[str, str] = {}
    removed: dict[str, str] = {}
    changed: dict[str, tuple[str, str]] = {}
    unchanged: list[str] = []

    all_keys = set(old_env) | set(new_env)
    for key in sorted(all_keys):
        if key not in old_env:
            added[key] = new_env[key]
        elif key not in new_env:
            removed[key] = old_env[key]
        elif old_env[key] != new_env[key]:
            changed[key] = (old_env[key], new_env[key])
        else:
            unchanged.append(key)

    return DiffResult(added=added, removed=removed, changed=changed, unchanged=unchanged)
