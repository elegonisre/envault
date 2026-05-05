"""Tests for envault.sharing — RSA-based key export/import for team sharing."""

import json
import pytest

from envault.sharing import export_key, generate_keypair, import_key


@pytest.fixture()
def keypair(tmp_path):
    priv = str(tmp_path / "test_private.pem")
    pub = str(tmp_path / "test_public.pem")
    generate_keypair(priv, pub)
    return priv, pub


class TestGenerateKeypair:
    def test_files_are_created(self, tmp_path):
        priv = str(tmp_path / "priv.pem")
        pub = str(tmp_path / "pub.pem")
        generate_keypair(priv, pub)
        assert (tmp_path / "priv.pem").exists()
        assert (tmp_path / "pub.pem").exists()

    def test_pem_headers(self, tmp_path):
        priv = str(tmp_path / "priv.pem")
        pub = str(tmp_path / "pub.pem")
        generate_keypair(priv, pub)
        assert b"PRIVATE KEY" in (tmp_path / "priv.pem").read_bytes()
        assert b"PUBLIC KEY" in (tmp_path / "pub.pem").read_bytes()


class TestExportKey:
    def test_returns_json_string(self, keypair):
        _, pub = keypair
        token = export_key("s3cr3t", pub)
        data = json.loads(token)
        assert "key" in data
        assert data["v"] == 1

    def test_different_ciphertexts_for_same_password(self, keypair):
        _, pub = keypair
        t1 = export_key("same_password", pub)
        t2 = export_key("same_password", pub)
        # OAEP uses random padding so tokens should differ
        assert json.loads(t1)["key"] != json.loads(t2)["key"]


class TestImportKey:
    def test_roundtrip(self, keypair):
        priv, pub = keypair
        password = "my_vault_password"
        token = export_key(password, pub)
        recovered = import_key(token, priv)
        assert recovered == password

    def test_wrong_private_key_raises(self, tmp_path, keypair):
        _, pub = keypair
        other_priv = str(tmp_path / "other_priv.pem")
        other_pub = str(tmp_path / "other_pub.pem")
        generate_keypair(other_priv, other_pub)
        token = export_key("secret", pub)
        with pytest.raises(Exception):
            import_key(token, other_priv)

    def test_unsupported_version_raises(self, keypair):
        priv, _ = keypair
        bad_token = json.dumps({"v": 99, "key": "abc"})
        with pytest.raises(ValueError, match="Unsupported token version"):
            import_key(bad_token, priv)
