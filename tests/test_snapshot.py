"""Tests for envault.snapshot."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.vault import encrypt_file
from envault.snapshot import (
    save_snapshot,
    restore_snapshot,
    list_snapshots,
    delete_snapshot,
    _snapshot_dir,
    _snap_path,
    _meta_path,
)

_PASSWORD = "s3cret"
_ENV_CONTENT = b"API_KEY=abc\nDB_URL=postgres://localhost/test\n"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / "test.env"
    env.write_bytes(_ENV_CONTENT)
    out = tmp_path / "test.env.vault"
    encrypt_file(env, out, _PASSWORD)
    return out


def test_save_snapshot_creates_files(vault_file):
    meta = save_snapshot(vault_file, "v1")
    assert _snap_path(vault_file, "v1").exists()
    assert _meta_path(vault_file, "v1").exists()
    assert meta.name == "v1"


def test_save_snapshot_meta_json(vault_file):
    save_snapshot(vault_file, "v1", note="initial")
    data = json.loads(_meta_path(vault_file, "v1").read_text())
    assert data["name"] == "v1"
    assert data["note"] == "initial"
    assert "created_at" in data


def test_save_snapshot_missing_vault(tmp_path):
    with pytest.raises(FileNotFoundError):
        save_snapshot(tmp_path / "nonexistent.vault", "v1")


def test_restore_snapshot_overwrites_vault(vault_file, tmp_path):
    original_bytes = vault_file.read_bytes()
    save_snapshot(vault_file, "v1")
    # tamper with vault
    vault_file.write_bytes(b"tampered")
    restore_snapshot(vault_file, "v1")
    assert vault_file.read_bytes() == original_bytes


def test_restore_snapshot_missing_raises(vault_file):
    with pytest.raises(FileNotFoundError):
        restore_snapshot(vault_file, "does_not_exist")


def test_list_snapshots_empty(vault_file):
    assert list_snapshots(vault_file) == []


def test_list_snapshots_returns_sorted(vault_file):
    save_snapshot(vault_file, "alpha")
    save_snapshot(vault_file, "beta")
    snaps = list_snapshots(vault_file)
    assert len(snaps) == 2
    assert snaps[0].name == "alpha"
    assert snaps[1].name == "beta"


def test_delete_snapshot_removes_files(vault_file):
    save_snapshot(vault_file, "v1")
    delete_snapshot(vault_file, "v1")
    assert not _snap_path(vault_file, "v1").exists()
    assert not _meta_path(vault_file, "v1").exists()


def test_delete_snapshot_not_in_list(vault_file):
    save_snapshot(vault_file, "v1")
    delete_snapshot(vault_file, "v1")
    assert list_snapshots(vault_file) == []


def test_snapshot_dir_inside_vault_parent(vault_file):
    sdir = _snapshot_dir(vault_file)
    assert sdir.parent == vault_file.parent
