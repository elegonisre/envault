"""Encryption and decryption utilities for envault."""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
ITERATIONS = 390000

# Minimum payload length: salt + nonce + GCM auth tag (16 bytes)
_MIN_PAYLOAD_SIZE = SALT_SIZE + NONCE_SIZE + 16


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from a password using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt(plaintext: str, password: str) -> str:
    """Encrypt plaintext with a password.

    Returns a base64-encoded string containing salt + nonce + ciphertext.
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    payload = salt + nonce + ciphertext
    return base64.b64encode(payload).decode("utf-8")


def decrypt(encoded: str, password: str) -> str:
    """Decrypt a base64-encoded payload produced by :func:`encrypt`.

    Raises ValueError on authentication failure or bad password.
    """
    try:
        payload = base64.b64decode(encoded.encode("utf-8"))
    except Exception as exc:
        raise ValueError("Invalid encoded payload.") from exc

    if len(payload) < _MIN_PAYLOAD_SIZE:
        raise ValueError(
            f"Payload too short: expected at least {_MIN_PAYLOAD_SIZE} bytes, "
            f"got {len(payload)}."
        )

    salt = payload[:SALT_SIZE]
    nonce = payload[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = payload[SALT_SIZE + NONCE_SIZE:]

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise ValueError("Decryption failed. Wrong password or corrupted data.") from exc

    return plaintext.decode("utf-8")
