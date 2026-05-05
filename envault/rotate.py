"""Key rotation support: re-encrypt a vault file with a new password."""

from __future__ import annotations

import os
from pathlib import Path

from envault.vault import decrypt_file, encrypt_file
from envault.audit import log_event


def rotate_key(
    vault_path: str | Path,
    old_password: str,
    new_password: str,
    output_path: str | Path | None = None,
    *,
    user: str | None = None,
    in_place: bool = False,
) -> Path:
    """Decrypt *vault_path* with *old_password* and re-encrypt with *new_password*.

    Parameters
    ----------
    vault_path:
        Path to the existing encrypted vault file.
    old_password:
        Password currently protecting the vault.
    new_password:
        New password to protect the vault after rotation.
    output_path:
        Destination path for the rotated vault.  Defaults to
        ``<vault_path>.rotated`` unless *in_place* is ``True``.
    user:
        Optional username recorded in the audit log.
    in_place:
        When ``True`` the original file is overwritten atomically.

    Returns
    -------
    Path
        Absolute path to the written (rotated) vault file.
    """
    vault_path = Path(vault_path)

    plaintext: str = decrypt_file(str(vault_path), old_password)

    if in_place:
        dest = vault_path
    elif output_path is not None:
        dest = Path(output_path)
    else:
        dest = vault_path.with_suffix(".rotated")

    if in_place:
        # Write to a temp file first, then replace atomically.
        tmp = dest.with_suffix(".tmp")
        try:
            encrypt_file(plaintext, str(tmp), new_password)
            os.replace(tmp, dest)
        finally:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
    else:
        encrypt_file(plaintext, str(dest), new_password)

    log_event(
        "rotate_key",
        user=user,
        details={"vault": str(vault_path.resolve()), "output": str(dest.resolve())},
    )

    return dest.resolve()
