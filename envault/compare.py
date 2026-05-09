"""Compare two vault files and report which keys differ in value."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.vault import decrypt_file


@dataclass
class CompareResult:
    only_in_old: List[str] = field(default_factory=list)
    only_in_new: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.only_in_old or self.only_in_new or self.changed)


def _parse_env(text: str) -> Dict[str, str]:
    """Parse decrypted env text into a key/value mapping."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def compare_vaults(
    old_path: str,
    new_path: str,
    old_password: str,
    new_password: Optional[str] = None,
) -> CompareResult:
    """Decrypt both vaults and compare their key/value pairs.

    If *new_password* is ``None`` the same password is used for both files.
    """
    if new_password is None:
        new_password = old_password

    old_text = decrypt_file(old_path, old_password)
    new_text = decrypt_file(new_path, new_password)

    old_env = _parse_env(old_text)
    new_env = _parse_env(new_text)

    old_keys = set(old_env)
    new_keys = set(new_env)

    result = CompareResult()
    result.only_in_old = sorted(old_keys - new_keys)
    result.only_in_new = sorted(new_keys - old_keys)

    for key in sorted(old_keys & new_keys):
        if old_env[key] == new_env[key]:
            result.unchanged.append(key)
        else:
            result.changed.append(key)

    return result
