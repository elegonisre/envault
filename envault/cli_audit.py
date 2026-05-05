"""CLI commands for viewing the envault audit log."""

import argparse
import json
import sys
from typing import Optional

from envault.audit import DEFAULT_AUDIT_FILE, read_log


def cmd_log(args: argparse.Namespace) -> None:
    """Print audit log entries to stdout."""
    entries = read_log(audit_file=args.audit_file)
    if not entries:
        print("No audit entries found.", file=sys.stderr)
        return

    if args.json:
        json.dump(entries, sys.stdout, indent=2)
        print()
        return

    limit = args.last if args.last else len(entries)
    for entry in entries[-limit:]:
        parts = [
            entry.get("timestamp", ""),
            f"[{entry.get('action', '?').upper()}]",
            entry.get("target", ""),
            f"by {entry.get('user', 'unknown')}",
        ]
        extra = {k: v for k, v in entry.items()
                 if k not in ("timestamp", "action", "target", "user")}
        if extra:
            parts.append(str(extra))
        print("  ".join(parts))


def build_audit_parser(
    parent: Optional[argparse._SubParsersAction] = None,
) -> argparse.ArgumentParser:
    kwargs = dict(description="Show envault audit log")
    if parent is not None:
        parser = parent.add_parser("log", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument(
        "--audit-file",
        default=DEFAULT_AUDIT_FILE,
        help="Path to audit log (default: %(default)s)",
    )
    parser.add_argument(
        "--last",
        type=int,
        default=0,
        metavar="N",
        help="Show only the last N entries",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output entries as JSON array",
    )
    parser.set_defaults(func=cmd_log)
    return parser
