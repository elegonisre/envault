"""CLI commands for vault access history."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.history import get_vault_history, format_history


def _prompt(msg: str) -> str:
    return input(msg).strip()


def cmd_history(args: argparse.Namespace) -> None:
    vault = Path(args.vault)
    if not vault.exists():
        print(f"error: vault file not found: {vault}", file=sys.stderr)
        sys.exit(1)

    limit = args.limit if args.limit and args.limit > 0 else None
    entries = get_vault_history(vault, limit=limit)

    if not entries:
        print(f"No history found for {vault}")
        return

    output = format_history(entries, fmt=args.format)
    print(output)


def build_history_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envault history",
        description="Show access history for a vault file.",
    )
    if parent is not None:
        parser = parent.add_parser("history", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("vault", help="Path to the encrypted vault file")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        metavar="N",
        help="Maximum number of entries to show (default: 20)",
    )
    parser.add_argument(
        "--format",
        choices=["plain", "json"],
        default="plain",
        help="Output format (default: plain)",
    )
    parser.set_defaults(func=cmd_history)
    return parser


if __name__ == "__main__":  # pragma: no cover
    _parser = build_history_parser()
    _args = _parser.parse_args()
    cmd_history(_args)
