"""CLI interface for the vault search feature."""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from envault.search import search_vaults


def _prompt(msg: str = "Vault password: ") -> str:  # pragma: no cover
    return getpass.getpass(msg)


def cmd_search(args: argparse.Namespace, password: str | None = None) -> None:
    """Execute the search sub-command."""
    pw = password or _prompt()
    vault_paths = [Path(p) for p in args.vaults]

    for vp in vault_paths:
        if not vp.exists():
            print(f"error: vault file not found: {vp}", file=sys.stderr)
            sys.exit(1)

    results = search_vaults(
        vault_paths,
        pw,
        args.pattern,
        search_values=args.values,
        ignore_case=args.ignore_case,
    )

    if not results:
        print("No matches found.")
        return

    current_vault = None
    for r in results:
        if r.vault_path != current_vault:
            current_vault = r.vault_path
            print(f"\n=== {r.vault_path} ===")
        if args.show_values:
            print(f"  line {r.line_number:>4}: {r.key}={r.value}")
        else:
            print(f"  line {r.line_number:>4}: {r.key}")


def build_search_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    kwargs = dict(
        description="Search for keys (or values) inside encrypted vault files."
    )
    if parent is not None:
        parser = parent.add_parser("search", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envault search", **kwargs)

    parser.add_argument("pattern", help="Regex pattern to search for")
    parser.add_argument("vaults", nargs="+", metavar="VAULT", help="Encrypted vault file(s)")
    parser.add_argument(
        "--values", action="store_true", default=False,
        help="Also search inside values (default: keys only)",
    )
    parser.add_argument(
        "--show-values", action="store_true", default=False,
        help="Print matched values in output",
    )
    parser.add_argument(
        "-i", "--ignore-case", action="store_true", default=False,
        help="Case-insensitive matching",
    )
    parser.set_defaults(func=cmd_search)
    return parser
