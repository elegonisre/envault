"""CLI commands for vault snapshot management."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from getpass import getpass

from envault.snapshot import save_snapshot, restore_snapshot, list_snapshots, delete_snapshot


def _prompt(msg: str) -> str:
    return getpass(msg)


def cmd_snapshot(args: argparse.Namespace) -> int:
    sub = args.snapshot_cmd

    if sub == "save":
        try:
            meta = save_snapshot(
                vault_path=Path(args.vault),
                name=args.name,
                note=args.note or "",
                user=args.user or None,
            )
            print(f"Snapshot '{meta.name}' saved at {meta.created_at}")
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    elif sub == "restore":
        try:
            restore_snapshot(
                vault_path=Path(args.vault),
                name=args.name,
                user=args.user or None,
            )
            print(f"Vault restored from snapshot '{args.name}'.")
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    elif sub == "list":
        snaps = list_snapshots(Path(args.vault))
        if not snaps:
            print("No snapshots found.")
        else:
            for s in snaps:
                note_part = f"  # {s.note}" if s.note else ""
                print(f"  {s.name:<20} {s.created_at}{note_part}")

    elif sub == "delete":
        delete_snapshot(
            vault_path=Path(args.vault),
            name=args.name,
            user=args.user or None,
        )
        print(f"Snapshot '{args.name}' deleted.")

    else:
        print("Unknown snapshot subcommand.", file=sys.stderr)
        return 1

    return 0


def build_snapshot_parser(parent_subparsers=None) -> argparse.ArgumentParser:
    kwargs = dict(description="Manage vault snapshots")
    if parent_subparsers:
        parser = parent_subparsers.add_parser("snapshot", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("vault", help="Path to the vault file")
    parser.add_argument("--user", default=None, help="Username for audit log")
    sub = parser.add_subparsers(dest="snapshot_cmd", required=True)

    p_save = sub.add_parser("save", help="Save a snapshot")
    p_save.add_argument("name", help="Snapshot name")
    p_save.add_argument("--note", default="", help="Optional note")

    p_restore = sub.add_parser("restore", help="Restore a snapshot")
    p_restore.add_argument("name", help="Snapshot name")

    sub.add_parser("list", help="List all snapshots")

    p_del = sub.add_parser("delete", help="Delete a snapshot")
    p_del.add_argument("name", help="Snapshot name")

    parser.set_defaults(func=cmd_snapshot)
    return parser
