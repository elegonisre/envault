"""CLI sub-command: diff two vault files."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.diff import diff_vaults


def _prompt(prompt_text: str) -> str:
    return getpass.getpass(prompt_text)


def _print_diff_results(result) -> None:
    """Print the diff results to stdout in a human-readable format."""
    for key, value in result.added.items():
        print(f"+ {key}={value}")
    for key, value in result.removed.items():
        print(f"- {key}={value}")
    for key, (old_val, new_val) in result.changed.items():
        print(f"~ {key}: {old_val!r} -> {new_val!r}")

    print(
        f"\nSummary: {len(result.added)} added, "
        f"{len(result.removed)} removed, "
        f"{len(result.changed)} changed, "
        f"{len(result.unchanged)} unchanged."
    )


def cmd_diff(args: argparse.Namespace) -> None:
    """Decrypt both vaults and print a human-readable diff."""
    password = _prompt("Password for OLD vault: ")
    if args.separate_passwords:
        new_password = _prompt("Password for NEW vault: ")
    else:
        new_password = password

    try:
        result = diff_vaults(args.old, args.new, password, new_password)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    total_changes = len(result.added) + len(result.removed) + len(result.changed)
    if total_changes == 0:
        print("No differences found.")
        return

    _print_diff_results(result)


def build_diff_parser(
    parent: argparse._SubParsersAction | None = None,
) -> argparse.ArgumentParser:
    kwargs: dict = dict(
        description="Show differences between two encrypted vault files."
    )
    if parent is not None:
        parser: argparse.ArgumentParser = parent.add_parser("diff", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envault diff", **kwargs)

    parser.add_argument("old", help="Path to the OLD vault file")
    parser.add_argument("new", help="Path to the NEW vault file")
    parser.add_argument(
        "--separate-passwords",
        action="store_true",
        default=False,
        help="Prompt for a different password for each vault",
    )
    parser.set_defaults(func=cmd_diff)
    return parser
