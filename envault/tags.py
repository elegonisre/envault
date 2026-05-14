"""Tag-based labelling for vault files."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

_TAGS_SUFFIX = ".tags.json"
_TAG_RE = re.compile(r"^[a-z0-9_\-]{1,32}$")


def _tags_path(vault_path: str | Path) -> Path:
    return Path(str(vault_path) + _TAGS_SUFFIX)


def _validate_tag(tag: str) -> None:
    if not _TAG_RE.match(tag):
        raise ValueError(
            f"Invalid tag {tag!r}: must be 1-32 lowercase alphanumeric, hyphen, or underscore characters."
        )


def read_tags(vault_path: str | Path) -> List[str]:
    """Return the list of tags associated with *vault_path*."""
    path = _tags_path(vault_path)
    if not path.exists():
        return []
    data: Dict = json.loads(path.read_text())
    return data.get("tags", [])


def write_tags(vault_path: str | Path, tags: List[str]) -> Path:
    """Persist *tags* for *vault_path* and return the tags-file path."""
    for tag in tags:
        _validate_tag(tag)
    unique = sorted(set(tags))
    path = _tags_path(vault_path)
    path.write_text(json.dumps({"tags": unique}, indent=2))
    return path


def add_tag(vault_path: str | Path, tag: str) -> List[str]:
    """Add *tag* to the vault's tag list and return the updated list."""
    _validate_tag(tag)
    current = read_tags(vault_path)
    if tag not in current:
        current.append(tag)
    write_tags(vault_path, current)
    return sorted(set(current))


def remove_tag(vault_path: str | Path, tag: str) -> List[str]:
    """Remove *tag* from the vault's tag list and return the updated list."""
    current = read_tags(vault_path)
    updated = [t for t in current if t != tag]
    write_tags(vault_path, updated)
    return updated


def find_vaults_by_tag(directory: str | Path, tag: str) -> List[Path]:
    """Return all vault paths in *directory* that carry *tag*."""
    directory = Path(directory)
    results: List[Path] = []
    for tags_file in sorted(directory.glob(f"*{_TAGS_SUFFIX}")):
        data: Dict = json.loads(tags_file.read_text())
        if tag in data.get("tags", []):
            vault = Path(str(tags_file)[: -len(_TAGS_SUFFIX)])
            results.append(vault)
    return results
