"""Lint an encrypted vault for common .env issues."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envault.vault import decrypt_file

_VALID_KEY_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')
_QUOTED_VALUE_RE = re.compile(r'^(['"])(.*?)\1$')
_WHITESPACE_VALUE_RE = re.compile(r'\s')


@dataclass
class LintIssue:
    line: int
    key: str | None
    message: str
    severity: str  # 'error' | 'warning'


@dataclass
class LintResult:
    path: Path
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == 'error' for i in self.issues)


def _check_line(lineno: int, raw: str) -> List[LintIssue]:
    issues: List[LintIssue] = []
    stripped = raw.strip()

    if not stripped or stripped.startswith('#'):
        return issues

    if '=' not in stripped:
        issues.append(LintIssue(lineno, None, 'Missing "=" separator', 'error'))
        return issues

    key, _, value = stripped.partition('=')
    key = key.strip()
    value = value.strip()

    if not _VALID_KEY_RE.match(key):
        issues.append(LintIssue(lineno, key,
                                f'Key "{key}" should be UPPER_SNAKE_CASE', 'warning'))

    if value == '':
        issues.append(LintIssue(lineno, key,
                                f'Key "{key}" has an empty value', 'warning'))
        return issues

    m = _QUOTED_VALUE_RE.match(value)
    if m:
        inner = m.group(2)
        if _WHITESPACE_VALUE_RE.search(inner) is None and len(inner) > 0:
            issues.append(LintIssue(lineno, key,
                                    f'Value for "{key}" is quoted but contains no whitespace',
                                    'warning'))
    elif _WHITESPACE_VALUE_RE.search(value):
        issues.append(LintIssue(lineno, key,
                                f'Value for "{key}" contains whitespace but is not quoted',
                                'error'))

    return issues


def lint_vault(vault_path: Path, password: str) -> LintResult:
    """Decrypt *vault_path* and lint its contents."""
    plaintext = decrypt_file(vault_path, password)
    result = LintResult(path=vault_path)
    for lineno, raw in enumerate(plaintext.splitlines(), start=1):
        result.issues.extend(_check_line(lineno, raw))
    return result
