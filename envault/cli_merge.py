"""CLI sub-command: envault merge."""
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from envault.merge import merge_vaults


def _prompt(msg: str) -> str:
    return getpass.getpass(msg)


def cmd_merge(args: argparse.Namespace) -> None:
    base_pw = _prompt(f"Password for base vault [{args.base}]: ")

    if args.separate_passwords:
        other_pw = _prompt(f"Password for other vault [{args.other}]: ")
    else:
        other_pw = base_pw

    out_pw = _prompt("Password for merged output vault: ")

    output = Path(args.output) if args.output else Path(args.base).with_suffix(".merged.vault")

    result = merge_vaults(
        base_path=Path(args.base),
        other_path=Path(args.other),
        base_password=base_pw,
        other_password=other_pw,
        output_path=output,
        out_password=out_pw,
        strategy=args.strategy,
    )

    print(f"Merged vault written to: {output}")
    print(f"  Keys added from other : {len(result.added)}")
    print(f"  Conflicts detected    : {len(result.conflicts)}")
    if result.conflicts:
        print(f"  Conflict keys         : {', '.join(result.conflicts)}")
        print(f"  Strategy applied      : {args.strategy}")
    if result.overwritten:
        print(f"  Keys overwritten      : {', '.join(result.overwritten)}")


def build_merge_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser("merge", help="Merge two encrypted vault files")
    p.add_argument("base", help="Base vault file (.vault)")
    p.add_argument("other", help="Other vault file to merge in (.vault)")
    p.add_argument("-o", "--output", default=None, help="Output path for merged vault")
    p.add_argument(
        "--strategy",
        choices=["ours", "theirs"],
        default="ours",
        help="Conflict resolution strategy (default: ours)",
    )
    p.add_argument(
        "--separate-passwords",
        action="store_true",
        default=False,
        help="Prompt for separate passwords for each vault",
    )
    p.set_defaults(func=cmd_merge)
    return p
