"""Search for keys across encrypted vault files."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.vault import decrypt_file


@dataclass
class SearchResult:
    vault_path: Path
    key: str
    value: str
    line_number: int


def _parse_env_lines(text: str):
    """Yield (line_number, key, value) for each valid KEY=VALUE line."""
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        yield i, key.strip(), value.strip()


def search_vault(
    vault_path: Path,
    password: str,
    pattern: str,
    search_values: bool = False,
    ignore_case: bool = False,
) -> List[SearchResult]:
    """Decrypt *vault_path* and return all entries whose key (or value) matches *pattern*."""
    plaintext = decrypt_file(vault_path, password)
    flags = re.IGNORECASE if ignore_case else 0
    compiled = re.compile(pattern, flags)

    results: List[SearchResult] = []
    for lineno, key, value in _parse_env_lines(plaintext):
        target = key if not search_values else f"{key}={value}"
        if compiled.search(target):
            results.append(SearchResult(vault_path=vault_path, key=key, value=value, line_number=lineno))
    return results


def search_vaults(
    vault_paths: List[Path],
    password: str,
    pattern: str,
    search_values: bool = False,
    ignore_case: bool = False,
) -> List[SearchResult]:
    """Search multiple vault files with the same password."""
    all_results: List[SearchResult] = []
    for path in vault_paths:
        all_results.extend(
            search_vault(path, password, pattern, search_values=search_values, ignore_case=ignore_case)
        )
    return all_results
