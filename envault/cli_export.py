"""CLI sub-command: export a vault to dotenv / JSON / shell format."""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from envault.export import export_vault


def _prompt(prompt_text: str) -> str:  # pragma: no cover
    return getpass.getpass(prompt_text)


def cmd_export(args: argparse.Namespace) -> None:
    """Handle the *export* sub-command."""
    password = getattr(args, "password", None) or _prompt("Vault password: ")

    output_path = getattr(args, "output", None)

    try:
        rendered = export_vault(
            vault_path=args.vault,
            password=password,
            fmt=args.format,
            output_path=output_path,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if output_path:
        print(f"Exported to {output_path}")
    else:
        sys.stdout.write(rendered)


def build_export_parser(
    subparsers: "argparse._SubParsersAction | None" = None,
) -> argparse.ArgumentParser:
    """Build (and optionally register) the export sub-command parser."""
    kwargs = dict(
        description="Export a decrypted vault to dotenv, JSON, or shell format."
    )
    if subparsers is not None:
        parser: argparse.ArgumentParser = subparsers.add_parser("export", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envault export", **kwargs)

    parser.add_argument("vault", help="Path to the encrypted .vault file")
    parser.add_argument(
        "--format",
        choices=["dotenv", "json", "shell"],
        default="dotenv",
        help="Output format (default: dotenv)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Write output to this file instead of stdout",
    )
    parser.add_argument(
        "--password", "-p",
        default=None,
        help="Vault password (omit to be prompted)",
    )
    parser.set_defaults(func=cmd_export)
    return parser
