"""Tests for envault.cli_snapshot."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault.vault import encrypt_file
from envault.snapshot import save_snapshot
from envault.cli_snapshot import build_snapshot_parser, cmd_snapshot

_PASSWORD = "s3cret"
_ENV_CONTENT = b"KEY=value\n"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / "test.env"
    env.write_bytes(_ENV_CONTENT)
    out = tmp_path / "test.env.vault"
    encrypt_file(env, out, _PASSWORD)
    return out


def _parse(vault: str, *args):
    parser = build_snapshot_parser()
    return parser.parse_args([vault, *args])


def test_build_snapshot_parser_returns_parser():
    p = build_snapshot_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_parser_save_subcommand(vault_file):
    ns = _parse(str(vault_file), "save", "v1")
    assert ns.snapshot_cmd == "save"
    assert ns.name == "v1"


def test_parser_save_with_note(vault_file):
    ns = _parse(str(vault_file), "save", "v1", "--note", "my note")
    assert ns.note == "my note"


def test_parser_list_subcommand(vault_file):
    ns = _parse(str(vault_file), "list")
    assert ns.snapshot_cmd == "list"


def test_parser_restore_subcommand(vault_file):
    ns = _parse(str(vault_file), "restore", "v1")
    assert ns.snapshot_cmd == "restore"
    assert ns.name == "v1"


def test_parser_delete_subcommand(vault_file):
    ns = _parse(str(vault_file), "delete", "v1")
    assert ns.snapshot_cmd == "delete"


def test_cmd_snapshot_save_returns_zero(vault_file):
    ns = _parse(str(vault_file), "save", "v1")
    assert cmd_snapshot(ns) == 0


def test_cmd_snapshot_list_returns_zero(vault_file, capsys):
    ns = _parse(str(vault_file), "list")
    assert cmd_snapshot(ns) == 0


def test_cmd_snapshot_list_shows_names(vault_file, capsys):
    save_snapshot(vault_file, "snap1", note="first")
    ns = _parse(str(vault_file), "list")
    cmd_snapshot(ns)
    out = capsys.readouterr().out
    assert "snap1" in out


def test_cmd_snapshot_restore_returns_zero(vault_file):
    save_snapshot(vault_file, "v1")
    ns = _parse(str(vault_file), "restore", "v1")
    assert cmd_snapshot(ns) == 0


def test_cmd_snapshot_save_missing_vault(tmp_path, capsys):
    ns = _parse(str(tmp_path / "ghost.vault"), "save", "v1")
    rc = cmd_snapshot(ns)
    assert rc == 1
    assert "Error" in capsys.readouterr().err
