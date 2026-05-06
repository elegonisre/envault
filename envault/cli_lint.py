"""CLI sub-command: lint an encrypted vault file."""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from envault.lint import lint_vault


def _prompt(prompt_text: str) -> str:  # pragma: no cover
    return getpass.getpass(prompt_text)


def cmd_lint(args: argparse.Namespace) -> int:
    password = args.password or _prompt('Vault password: ')
    vault_path = Path(args.vault)

    if not vault_path.exists():
        print(f'error: file not found: {vault_path}', file=sys.stderr)
        return 1

    try:
        result = lint_vault(vault_path, password)
    except Exception as exc:  # noqa: BLE001
        print(f'error: could not decrypt vault — {exc}', file=sys.stderr)
        return 1

    if not result.issues:
        print(f'✔  {vault_path}: no issues found')
        return 0

    for issue in result.issues:
        loc = f'{vault_path}:{issue.line}'
        key_info = f' [{issue.key}]' if issue.key else ''
        tag = 'ERROR  ' if issue.severity == 'error' else 'WARNING'
        print(f'{tag}  {loc}{key_info}  {issue.message}')

    errors = sum(1 for i in result.issues if i.severity == 'error')
    warnings = sum(1 for i in result.issues if i.severity == 'warning')
    summary = []
    if errors:
        summary.append(f'{errors} error(s)')
    if warnings:
        summary.append(f'{warnings} warning(s)')
    print('\n' + ', '.join(summary))

    return 0 if result.ok else 1


def build_lint_parser(subparsers=None) -> argparse.ArgumentParser:
    kwargs = dict(
        description='Lint an encrypted .env vault for common issues',
    )
    if subparsers is None:
        parser = argparse.ArgumentParser(**kwargs)
    else:
        parser = subparsers.add_parser('lint', **kwargs)

    parser.add_argument('vault', help='Path to the encrypted vault file')
    parser.add_argument(
        '--password', default=None,
        help='Vault password (prompted if omitted)',
    )
    parser.set_defaults(func=cmd_lint)
    return parser
