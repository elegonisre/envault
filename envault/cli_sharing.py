"""CLI sub-commands for recipient-based (asymmetric) vault sharing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.recipients import (
    decrypt_share,
    encrypt_for_recipients,
    read_recipients_file,
    write_recipients_file,
)
from envault.sharing import import_key
from envault.vault import decrypt_file, encrypt_file


def cmd_add_recipients(args: argparse.Namespace) -> None:
    """Encrypt the vault's symmetric password for each recipient public key."""
    password = args.password.encode() if args.password else _prompt_password()
    pub_keys = args.public_keys  # list of paths
    shares = encrypt_for_recipients(password, pub_keys)
    out_path = args.output or "recipients.json"
    write_recipients_file(shares, out_path)
    print(f"[envault] Encrypted shares written to {out_path} for {len(shares)} recipient(s).")


def cmd_decrypt_as_recipient(args: argparse.Namespace) -> None:
    """Decrypt vault using a recipient's private key to recover the password."""
    shares = read_recipients_file(args.recipients_file)
    recipient_id = Path(args.private_key).stem.replace("_private", "") + "_public"
    if recipient_id not in shares:
        # Fallback: try stem directly
        recipient_id = Path(args.private_key).stem

    if recipient_id not in shares:
        print(
            f"[envault] Error: no share found for '{recipient_id}' in {args.recipients_file}.",
            file=sys.stderr,
        )
        sys.exit(1)

    priv_key = import_key(args.private_key)
    password = decrypt_share(priv_key, shares[recipient_id])  # type: ignore[arg-type]
    output = args.output or args.vault_file.replace(".vault", ".env")
    decrypt_file(args.vault_file, output, password.decode())
    print(f"[envault] Decrypted vault written to {output}")


def _prompt_password() -> bytes:
    import getpass

    return getpass.getpass("Password: ").encode()


def build_sharing_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register sharing sub-commands onto an existing subparsers group."""
    # add-recipients
    p_add = subparsers.add_parser(
        "add-recipients",
        help="Encrypt vault password for one or more recipients' public keys",
    )
    p_add.add_argument("public_keys", nargs="+", help="Paths to recipient public key PEM files")
    p_add.add_argument("--password", default=None, help="Vault password (prompted if omitted)")
    p_add.add_argument("-o", "--output", default="recipients.json", help="Output JSON file")
    p_add.set_defaults(func=cmd_add_recipients)

    # decrypt-as-recipient
    p_dec = subparsers.add_parser(
        "decrypt-as-recipient",
        help="Decrypt vault using your private key via a recipients file",
    )
    p_dec.add_argument("vault_file", help="Path to the encrypted .vault file")
    p_dec.add_argument("private_key", help="Path to your private key PEM file")
    p_dec.add_argument("recipients_file", help="Path to the recipients.json file")
    p_dec.add_argument("-o", "--output", default=None, help="Output .env file path")
    p_dec.set_defaults(func=cmd_decrypt_as_recipient)
