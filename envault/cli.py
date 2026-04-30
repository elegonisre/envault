"""Command-line interface for envault."""

import sys
import getpass
import argparse
from pathlib import Path

from envault.vault import encrypt_file, decrypt_file


def get_password(confirm: bool = False) -> str:
    """Prompt the user for a password, optionally confirming it."""
    password = getpass.getpass("Password: ")
    if confirm:
        confirmation = getpass.getpass("Confirm password: ")
        if password != confirmation:
            print("Error: passwords do not match.", file=sys.stderr)
            sys.exit(1)
    return password


def cmd_encrypt(args: argparse.Namespace) -> None:
    """Handle the 'encrypt' subcommand."""
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".env.vault")

    if not input_path.exists():
        print(f"Error: input file '{input_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    password = get_password(confirm=True)
    encrypt_file(str(input_path), str(output_path), password)
    print(f"Encrypted '{input_path}' -> '{output_path}'")


def cmd_decrypt(args: argparse.Namespace) -> None:
    """Handle the 'decrypt' subcommand."""
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_suffix("")

    if not input_path.exists():
        print(f"Error: input file '{input_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    password = get_password(confirm=False)
    try:
        decrypt_file(str(input_path), str(output_path), password)
        print(f"Decrypted '{input_path}' -> '{output_path}'")
    except Exception:
        print("Error: decryption failed. Wrong password or corrupted file.", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Encrypt and manage .env files with team-sharing support.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    enc = subparsers.add_parser("encrypt", help="Encrypt a .env file.")
    enc.add_argument("input", help="Path to the plaintext .env file.")
    enc.add_argument("-o", "--output", help="Path for the encrypted output file.")

    dec = subparsers.add_parser("decrypt", help="Decrypt a .env.vault file.")
    dec.add_argument("input", help="Path to the encrypted .env.vault file.")
    dec.add_argument("-o", "--output", help="Path for the decrypted output file.")

    return parser


def main() -> None:
    """Entry point for the envault CLI."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "encrypt":
        cmd_encrypt(args)
    elif args.command == "decrypt":
        cmd_decrypt(args)


if __name__ == "__main__":
    main()
