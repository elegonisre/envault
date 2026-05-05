"""CLI sub-command for key rotation."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from envault.rotate import rotate_key


def _prompt(prompt: str) -> str:
    return getpass.getpass(prompt)


def _validate_new_password(new_password: str, confirm: str) -> None:
    """Validate that the new password meets basic requirements.

    Raises ``SystemExit`` with an informative message if validation fails.
    """
    if new_password != confirm:
        print("error: passwords do not match.", file=sys.stderr)
        sys.exit(1)
    if not new_password:
        print("error: new password must not be empty.", file=sys.stderr)
        sys.exit(1)


def cmd_rotate(args: argparse.Namespace) -> None:  # noqa: D401
    """Handler for the ``rotate`` sub-command."""
    vault = Path(args.vault)
    if not vault.exists():
        print(f"error: vault file not found: {vault}", file=sys.stderr)
        sys.exit(1)

    old_password = _prompt("Current password: ")
    new_password = _prompt("New password: ")
    confirm = _prompt("Confirm new password: ")

    _validate_new_password(new_password, confirm)

    try:
        output = rotate_key(
            vault,
            old_password,
            new_password,
            output_path=args.output,
            user=args.user,
            in_place=args.in_place,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Rotated vault written to: {output}")


def build_rotate_parser(subparsers: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: SLF001
    """Build (or attach) the argument parser for the rotate command."""
    kwargs: dict = dict(
        description="Re-encrypt a vault file with a new password.",
        help="Rotate the encryption key of a vault file.",
    )
    if subparsers is not None:
        parser: argparse.ArgumentParser = subparsers.add_parser("rotate", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envault rotate", **kwargs)

    parser.add_argument("vault", help="Path to the encrypted vault file.")
    parser.add_argument("-o", "--output", default=None, help="Output path for the rotated vault.")
    parser.add_argument(
        "--in-place",
        action="store_true",
        default=False,
        help="Overwrite the original vault file in-place.",
    )
    parser.add_argument("--user", default=None, help="Username to record in the audit log.")
    parser.set_defaults(func=cmd_rotate)
    return parser
