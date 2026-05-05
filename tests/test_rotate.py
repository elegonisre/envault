"""Tests for envault.rotate and envault.cli_rotate."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.vault import encrypt_file, decrypt_file
from envault.rotate import rotate_key
from envault.cli_rotate import build_rotate_parser, cmd_rotate


PLAINTEXT = "DB_HOST=localhost\nDB_PASS=secret\n"
OLD_PASS = "old-hunter2"
NEW_PASS = "new-hunter3"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "test.env.vault"
    encrypt_file(PLAINTEXT, str(path), OLD_PASS)
    return path


# ---------------------------------------------------------------------------
# rotate_key unit tests
# ---------------------------------------------------------------------------

class TestRotateKey:
    def test_returns_path(self, vault_file: Path) -> None:
        result = rotate_key(vault_file, OLD_PASS, NEW_PASS)
        assert isinstance(result, Path)

    def test_default_output_suffix(self, vault_file: Path) -> None:
        result = rotate_key(vault_file, OLD_PASS, NEW_PASS)
        assert result.suffix == ".rotated"

    def test_rotated_file_decryptable_with_new_password(self, vault_file: Path) -> None:
        result = rotate_key(vault_file, OLD_PASS, NEW_PASS)
        recovered = decrypt_file(str(result), NEW_PASS)
        assert recovered == PLAINTEXT

    def test_old_password_no_longer_works(self, vault_file: Path) -> None:
        result = rotate_key(vault_file, OLD_PASS, NEW_PASS)
        with pytest.raises(Exception):
            decrypt_file(str(result), OLD_PASS)

    def test_custom_output_path(self, vault_file: Path, tmp_path: Path) -> None:
        out = tmp_path / "rotated.vault"
        result = rotate_key(vault_file, OLD_PASS, NEW_PASS, output_path=out)
        assert result == out.resolve()
        assert out.exists()

    def test_in_place_overwrites_original(self, vault_file: Path) -> None:
        rotate_key(vault_file, OLD_PASS, NEW_PASS, in_place=True)
        recovered = decrypt_file(str(vault_file), NEW_PASS)
        assert recovered == PLAINTEXT

    def test_wrong_old_password_raises(self, vault_file: Path) -> None:
        with pytest.raises(Exception):
            rotate_key(vault_file, "wrong-password", NEW_PASS)


# ---------------------------------------------------------------------------
# cli_rotate tests
# ---------------------------------------------------------------------------

def test_build_rotate_parser_returns_parser() -> None:
    parser = build_rotate_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_parser_has_vault_argument() -> None:
    parser = build_rotate_parser()
    args = parser.parse_args(["my.vault"])
    assert args.vault == "my.vault"


def test_parser_in_place_flag() -> None:
    parser = build_rotate_parser()
    args = parser.parse_args(["my.vault", "--in-place"])
    assert args.in_place is True


def test_cmd_rotate_success(vault_file: Path, capsys) -> None:
    parser = build_rotate_parser()
    args = parser.parse_args([str(vault_file)])

    with patch("envault.cli_rotate._prompt", side_effect=[OLD_PASS, NEW_PASS, NEW_PASS]):
        cmd_rotate(args)

    captured = capsys.readouterr()
    assert "Rotated vault written to" in captured.out


def test_cmd_rotate_password_mismatch_exits(vault_file: Path) -> None:
    parser = build_rotate_parser()
    args = parser.parse_args([str(vault_file)])

    with patch("envault.cli_rotate._prompt", side_effect=[OLD_PASS, NEW_PASS, "different"]):
        with pytest.raises(SystemExit) as exc_info:
            cmd_rotate(args)
    assert exc_info.value.code == 1
