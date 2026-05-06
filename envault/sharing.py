"""Team-sharing support: export/import vault keys encrypted with RSA public keys."""

import base64
import json
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend


def generate_keypair(private_key_path: str, public_key_path: str) -> None:
    """Generate an RSA keypair and write PEM files to the given paths."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    Path(private_key_path).write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    Path(public_key_path).write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )


def export_key(password: str, public_key_path: str) -> str:
    """Encrypt *password* with an RSA public key and return a JSON token string."""
    pub_key_bytes = Path(public_key_path).read_bytes()
    public_key = serialization.load_pem_public_key(pub_key_bytes, backend=default_backend())
    ciphertext = public_key.encrypt(
        password.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    token = {"v": 1, "key": base64.b64encode(ciphertext).decode()}
    return json.dumps(token)


def import_key(token: str, private_key_path: str) -> str:
    """Decrypt a token produced by *export_key* using the RSA private key."""
    try:
        data = json.loads(token)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid token: not valid JSON") from exc
    if data.get("v") != 1:
        raise ValueError(f"Unsupported token version: {data.get('v')}")
    if "key" not in data:
        raise ValueError("Invalid token: missing 'key' field")
    ciphertext = base64.b64decode(data["key"])
    priv_key_bytes = Path(private_key_path).read_bytes()
    private_key = serialization.load_pem_private_key(
        priv_key_bytes, password=None, backend=default_backend()
    )
    plaintext = private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return plaintext.decode()
