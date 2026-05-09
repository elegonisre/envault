"""CLI interface for the vault compare feature."""

from __future__ import annotations

import argparse
import getpass
import sys

from envault.compare import compare_vaults


def _prompt(label: str) -> str:
    return getpass.getpass(label)


def cmd_compare(args: argparse.Namespace) -> None:
    old_password = _prompt(f"Password for '{args.old}': ")

    if args.separate_passwords:
        new_password = _prompt(f"Password for '{args.new}': ")
    else:
        new_password = None

    try:
        result = compare_vaults(args.old, args.new, old_password, new_password)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not result.has_differences:
        print("Vaults are identical.")
        return

    if result.only_in_old:
        print("Only in old vault:")
        for key in result.only_in_old:
            print(f"  - {key}")

    if result.only_in_new:
        print("Only in new vault:")
        for key in result.only_in_new:
            print(f"  + {key}")

    if result.changed:
        print("Changed keys:")
        for key in result.changed:
            print(f"  ~ {key}")

    if args.show_unchanged and result.unchanged:
        print("Unchanged keys:")
        for key in result.unchanged:
            print(f"    {key}")


def build_compare_parser(
    parent: "argparse._SubParsersAction | None" = None,
) -> argparse.ArgumentParser:
    kwargs = dict(
        description="Compare keys and values between two encrypted vault files."
    )
    if parent is not None:
        parser = parent.add_parser("compare", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envault-compare", **kwargs)

    parser.add_argument("old", help="Path to the older vault file")
    parser.add_argument("new", help="Path to the newer vault file")
    parser.add_argument(
        "--separate-passwords",
        action="store_true",
        default=False,
        help="Prompt for a different password for each vault",
    )
    parser.add_argument(
        "--show-unchanged",
        action="store_true",
        default=False,
        help="Also list keys that are identical in both vaults",
    )
    parser.set_defaults(func=cmd_compare)
    return parser


if __name__ == "__main__":  # pragma: no cover
    _parser = build_compare_parser()
    cmd_compare(_parser.parse_args())
