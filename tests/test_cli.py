"""Tests for the envault CLI."""

import sys
import pytest
from pathlib import Path
from unittest.mock import patch

from envault.cli import build_parser, cmd_encrypt, cmd_decrypt, main


PASSWORD = "cli-test-secret"
SAMPLE_ENV = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc123\n"


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(SAMPLE_ENV)
    return p


@pytest.fixture()
def vault_file(tmp_path: Path, env_file: Path) -> Path:
    """Pre-encrypted vault file for decrypt tests."""
    from envault.vault import encrypt_file

    out = tmp_path / ".env.vault"
    encrypt_file(str(env_file), str(out), PASSWORD)
    return out


class TestBuildParser:
    def test_encrypt_subcommand_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["encrypt", ".env"])
        assert args.command == "encrypt"
        assert args.input == ".env"
        assert args.output is None

    def test_encrypt_with_output(self):
        parser = build_parser()
        args = parser.parse_args(["encrypt", ".env", "-o", "out.vault"])
        assert args.output == "out.vault"

    def test_decrypt_subcommand_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["decrypt", ".env.vault"])
        assert args.command == "decrypt"

    def test_missing_subcommand_exits(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])


class TestCmdEncrypt:
    def test_encrypt_creates_output(self, env_file: Path, tmp_path: Path):
        out = tmp_path / "out.vault"
        args = build_parser().parse_args(["encrypt", str(env_file), "-o", str(out)])
        with patch("envault.cli.get_password", return_value=PASSWORD):
            cmd_encrypt(args)
        assert out.exists()
        assert out.read_bytes() != SAMPLE_ENV.encode()

    def test_encrypt_default_output_name(self, env_file: Path):
        args = build_parser().parse_args(["encrypt", str(env_file)])
        with patch("envault.cli.get_password", return_value=PASSWORD):
            cmd_encrypt(args)
        expected = env_file.with_suffix(".env.vault")
        assert expected.exists()

    def test_encrypt_missing_input_exits(self, tmp_path: Path):
        args = build_parser().parse_args(["encrypt", str(tmp_path / "nonexistent.env")])
        with pytest.raises(SystemExit):
            cmd_encrypt(args)


class TestCmdDecrypt:
    def test_decrypt_restores_content(self, vault_file: Path, tmp_path: Path):
        out = tmp_path / "restored.env"
        args = build_parser().parse_args(["decrypt", str(vault_file), "-o", str(out)])
        with patch("envault.cli.get_password", return_value=PASSWORD):
            cmd_decrypt(args)
        assert out.read_text() == SAMPLE_ENV

    def test_decrypt_wrong_password_exits(self, vault_file: Path, tmp_path: Path):
        out = tmp_path / "restored.env"
        args = build_parser().parse_args(["decrypt", str(vault_file), "-o", str(out)])
        with patch("envault.cli.get_password", return_value="wrong-password"):
            with pytest.raises(SystemExit):
                cmd_decrypt(args)

    def test_decrypt_missing_input_exits(self, tmp_path: Path):
        args = build_parser().parse_args(["decrypt", str(tmp_path / "missing.vault")])
        with pytest.raises(SystemExit):
            cmd_decrypt(args)
