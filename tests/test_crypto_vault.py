"""Tests for envault.crypto and envault.vault."""

import pytest
from pathlib import Path
from envault.crypto import encrypt, decrypt
from envault.vault import encrypt_file, decrypt_file


# ---------------------------------------------------------------------------
# crypto unit tests
# ---------------------------------------------------------------------------

class TestCrypto:
    PASSWORD = "super-secret-password"
    PLAINTEXT = "DATABASE_URL=postgres://localhost/mydb\nSECRET_KEY=abc123\n"

    def test_encrypt_returns_string(self):
        token = encrypt(self.PLAINTEXT, self.PASSWORD)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_roundtrip(self):
        token = encrypt(self.PLAINTEXT, self.PASSWORD)
        result = decrypt(token, self.PASSWORD)
        assert result == self.PLAINTEXT

    def test_different_ciphertexts_for_same_input(self):
        """Each encryption call should produce a unique token (random nonce/salt)."""
        t1 = encrypt(self.PLAINTEXT, self.PASSWORD)
        t2 = encrypt(self.PLAINTEXT, self.PASSWORD)
        assert t1 != t2

    def test_wrong_password_raises(self):
        token = encrypt(self.PLAINTEXT, self.PASSWORD)
        with pytest.raises(ValueError):
            decrypt(token, "wrong-password")

    def test_corrupted_payload_raises(self):
        with pytest.raises(ValueError):
            decrypt("notvalidbase64!!!", self.PASSWORD)


# ---------------------------------------------------------------------------
# vault integration tests
# ---------------------------------------------------------------------------

class TestVault:
    PASSWORD = "vault-password-42"
    ENV_CONTENT = "API_KEY=test123\nDEBUG=true\n"

    def test_encrypt_file_creates_vault(self, tmp_path: Path):
        env_file = tmp_path / ".env"
        env_file.write_text(self.ENV_CONTENT, encoding="utf-8")
        vault_file = encrypt_file(env_file, self.PASSWORD)
        assert vault_file.exists()
        assert vault_file.suffix == ".vault"

    def test_decrypt_file_restores_content(self, tmp_path: Path):
        env_file = tmp_path / ".env"
        env_file.write_text(self.ENV_CONTENT, encoding="utf-8")
        vault_file = encrypt_file(env_file, self.PASSWORD)
        env_file.unlink()  # remove original
        restored = decrypt_file(vault_file, self.PASSWORD)
        assert restored.read_text(encoding="utf-8") == self.ENV_CONTENT

    def test_encrypt_custom_output_path(self, tmp_path: Path):
        env_file = tmp_path / ".env"
        env_file.write_text(self.ENV_CONTENT, encoding="utf-8")
        out = tmp_path / "custom.vault"
        result = encrypt_file(env_file, self.PASSWORD, output_path=out)
        assert result == out
        assert out.exists()

    def test_encrypt_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            encrypt_file(tmp_path / "nonexistent.env", self.PASSWORD)

    def test_decrypt_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            decrypt_file(tmp_path / "nonexistent.vault", self.PASSWORD)

    def test_decrypt_wrong_password_raises(self, tmp_path: Path):
        env_file = tmp_path / ".env"
        env_file.write_text(self.ENV_CONTENT, encoding="utf-8")
        vault_file = encrypt_file(env_file, self.PASSWORD)
        with pytest.raises(ValueError):
            decrypt_file(vault_file, "wrong-password")
