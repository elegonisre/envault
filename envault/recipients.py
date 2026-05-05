"""Recipient-based encryption: encrypt vault secrets for multiple public keys."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

from envault.sharing import import_key


def encrypt_for_recipients(
    plaintext_key: bytes,
    recipient_pub_key_paths: List[str | Path],
) -> dict:
    """Encrypt a symmetric key for each recipient's public key.

    Returns a dict mapping recipient key fingerprint -> base64-encoded ciphertext.
    """
    import base64

    encrypted_shares: dict[str, str] = {}

    for pub_path in recipient_pub_key_paths:
        pub_key: RSAPublicKey = import_key(str(pub_path))  # type: ignore[assignment]
        ciphertext = pub_key.encrypt(
            plaintext_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        # Use the filename stem as a human-readable recipient identifier
        recipient_id = Path(pub_path).stem
        encrypted_shares[recipient_id] = base64.b64encode(ciphertext).decode()

    return encrypted_shares


def decrypt_share(private_key: RSAPrivateKey, encrypted_share_b64: str) -> bytes:
    """Decrypt a single encrypted share using the recipient's private key."""
    import base64

    ciphertext = base64.b64decode(encrypted_share_b64)
    return private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def write_recipients_file(shares: dict, output_path: str | Path) -> None:
    """Persist encrypted shares to a JSON file."""
    Path(output_path).write_text(json.dumps(shares, indent=2))


def read_recipients_file(path: str | Path) -> dict:
    """Load encrypted shares from a JSON file."""
    return json.loads(Path(path).read_text())
