"""High-level vault operations: encrypt/decrypt .env files."""

from pathlib import Path
from envault.crypto import encrypt, decrypt

VAULT_EXTENSION = ".vault"


def encrypt_file(env_path: str | Path, password: str, output_path: str | Path | None = None) -> Path:
    """Encrypt a .env file and write the result to *output_path*.

    If *output_path* is omitted the encrypted file is placed next to the
    source with a ``.vault`` extension appended.

    Returns the path of the written vault file.
    """
    env_path = Path(env_path)
    if not env_path.exists():
        raise FileNotFoundError(f"Source file not found: {env_path}")

    plaintext = env_path.read_text(encoding="utf-8")
    token = encrypt(plaintext, password)

    if output_path is None:
        output_path = env_path.with_suffix(env_path.suffix + VAULT_EXTENSION)
    output_path = Path(output_path)
    output_path.write_text(token, encoding="utf-8")
    return output_path


def decrypt_file(vault_path: str | Path, password: str, output_path: str | Path | None = None) -> Path:
    """Decrypt a vault file and write the plaintext .env to *output_path*.

    If *output_path* is omitted the decrypted file is placed next to the
    vault file with the ``.vault`` suffix stripped.

    Returns the path of the written .env file.
    """
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault file not found: {vault_path}")

    token = vault_path.read_text(encoding="utf-8")
    plaintext = decrypt(token, password)

    if output_path is None:
        stem = vault_path.name
        if stem.endswith(VAULT_EXTENSION):
            stem = stem[: -len(VAULT_EXTENSION)]
        output_path = vault_path.parent / stem
    output_path = Path(output_path)
    output_path.write_text(plaintext, encoding="utf-8")
    return output_path
