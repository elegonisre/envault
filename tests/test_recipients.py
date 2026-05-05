"""Tests for envault.recipients module."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from envault.sharing import generate_keypair, import_key
from envault.recipients import (
    decrypt_share,
    encrypt_for_recipients,
    read_recipients_file,
    write_recipients_file,
)


@pytest.fixture()
def keypair_dir(tmp_path: Path):
    """Generate two keypairs and return their paths."""
    pairs = []
    for name in ("alice", "bob"):
        priv = tmp_path / f"{name}_private.pem"
        pub = tmp_path / f"{name}_public.pem"
        generate_keypair(str(priv), str(pub))
        pairs.append({"priv": priv, "pub": pub, "name": name})
    return pairs


SECRET_KEY = b"super-secret-symmetric-key-32b!!"


def test_encrypt_for_recipients_returns_dict(keypair_dir, tmp_path):
    pub_paths = [p["pub"] for p in keypair_dir]
    shares = encrypt_for_recipients(SECRET_KEY, pub_paths)
    assert isinstance(shares, dict)
    assert len(shares) == 2
    assert "alice_public" in shares
    assert "bob_public" in shares


def test_encrypted_shares_are_base64_strings(keypair_dir):
    import base64

    pub_paths = [p["pub"] for p in keypair_dir]
    shares = encrypt_for_recipients(SECRET_KEY, pub_paths)
    for value in shares.values():
        assert isinstance(value, str)
        decoded = base64.b64decode(value)
        assert len(decoded) > 0


def test_decrypt_share_recovers_original(keypair_dir):
    alice = keypair_dir[0]
    shares = encrypt_for_recipients(SECRET_KEY, [alice["pub"]])
    priv_key = import_key(str(alice["priv"]))
    recovered = decrypt_share(priv_key, shares["alice_public"])  # type: ignore[arg-type]
    assert recovered == SECRET_KEY


def test_each_recipient_can_decrypt_independently(keypair_dir):
    pub_paths = [p["pub"] for p in keypair_dir]
    shares = encrypt_for_recipients(SECRET_KEY, pub_paths)
    for pair in keypair_dir:
        priv_key = import_key(str(pair["priv"]))
        share_id = f"{pair['name']}_public"
        recovered = decrypt_share(priv_key, shares[share_id])  # type: ignore[arg-type]
        assert recovered == SECRET_KEY


def test_write_and_read_recipients_file(keypair_dir, tmp_path):
    pub_paths = [p["pub"] for p in keypair_dir]
    shares = encrypt_for_recipients(SECRET_KEY, pub_paths)
    out_file = tmp_path / "recipients.json"
    write_recipients_file(shares, out_file)
    assert out_file.exists()
    loaded = read_recipients_file(out_file)
    assert loaded == shares


def test_recipients_file_is_valid_json(keypair_dir, tmp_path):
    pub_paths = [p["pub"] for p in keypair_dir]
    shares = encrypt_for_recipients(SECRET_KEY, pub_paths)
    out_file = tmp_path / "recipients.json"
    write_recipients_file(shares, out_file)
    content = out_file.read_text()
    parsed = json.loads(content)
    assert isinstance(parsed, dict)
