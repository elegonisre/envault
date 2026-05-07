"""Integration test: snapshot operations emit audit log entries."""
from __future__ import annotations

from pathlib import Path

import pytest

from envault.vault import encrypt_file
from envault.snapshot import save_snapshot, restore_snapshot, delete_snapshot
from envault.audit import read_log, clear_log, _audit_path

_PASSWORD = "s3cret"


@pytest.fixture(autouse=True)
def clean_audit(tmp_path, monkeypatch):
    """Redirect audit log to a temp file for each test."""
    log_file = tmp_path / "audit.log"
    monkeypatch.setattr("envault.audit._audit_path", lambda: log_file)
    yield log_file


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / "test.env"
    env.write_bytes(b"KEY=val\n")
    out = tmp_path / "test.env.vault"
    encrypt_file(env, out, _PASSWORD)
    return out


def test_save_snapshot_logs_event(vault_file, clean_audit):
    save_snapshot(vault_file, "v1", user="alice")
    entries = read_log(clean_audit)
    assert any(e["event"] == "snapshot_save" for e in entries)


def test_save_snapshot_log_contains_user(vault_file, clean_audit):
    save_snapshot(vault_file, "v1", user="alice")
    entries = read_log(clean_audit)
    save_entry = next(e for e in entries if e["event"] == "snapshot_save")
    assert save_entry.get("user") == "alice"


def test_restore_snapshot_logs_event(vault_file, clean_audit):
    save_snapshot(vault_file, "v1")
    restore_snapshot(vault_file, "v1", user="bob")
    entries = read_log(clean_audit)
    assert any(e["event"] == "snapshot_restore" for e in entries)


def test_delete_snapshot_logs_event(vault_file, clean_audit):
    save_snapshot(vault_file, "v1")
    delete_snapshot(vault_file, "v1", user="carol")
    entries = read_log(clean_audit)
    assert any(e["event"] == "snapshot_delete" for e in entries)


def test_multiple_saves_all_logged(vault_file, clean_audit):
    save_snapshot(vault_file, "v1")
    save_snapshot(vault_file, "v2")
    entries = read_log(clean_audit)
    save_events = [e for e in entries if e["event"] == "snapshot_save"]
    assert len(save_events) == 2
