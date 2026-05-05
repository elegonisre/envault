"""Tests for envault.audit module."""

import json
import os
import pytest
from pathlib import Path

from envault.audit import log_event, read_log, clear_log


@pytest.fixture()
def audit_log(tmp_path):
    """Return a temporary audit log path."""
    return str(tmp_path / "test_audit.log")


def test_log_event_creates_file(audit_log):
    log_event("encrypt", "secrets.env", audit_file=audit_log)
    assert Path(audit_log).exists()


def test_log_event_returns_dict(audit_log):
    entry = log_event("encrypt", "secrets.env", audit_file=audit_log)
    assert isinstance(entry, dict)
    assert entry["action"] == "encrypt"
    assert entry["target"] == "secrets.env"


def test_log_event_contains_timestamp(audit_log):
    entry = log_event("decrypt", "secrets.env.vault", audit_file=audit_log)
    assert "timestamp" in entry
    assert "T" in entry["timestamp"]  # ISO format


def test_log_event_uses_provided_user(audit_log):
    entry = log_event("encrypt", "f.env", user="alice", audit_file=audit_log)
    assert entry["user"] == "alice"


def test_log_event_extra_fields(audit_log):
    entry = log_event(
        "share", "f.env", extra={"recipients": 3}, audit_file=audit_log
    )
    assert entry["recipients"] == 3


def test_read_log_empty_when_no_file(tmp_path):
    entries = read_log(audit_file=str(tmp_path / "nonexistent.log"))
    assert entries == []


def test_read_log_returns_all_entries(audit_log):
    for action in ("encrypt", "decrypt", "share"):
        log_event(action, "f.env", audit_file=audit_log)
    entries = read_log(audit_file=audit_log)
    assert len(entries) == 3
    assert [e["action"] for e in entries] == ["encrypt", "decrypt", "share"]


def test_read_log_valid_json_per_line(audit_log):
    log_event("encrypt", "secrets.env", audit_file=audit_log)
    with open(audit_log) as fh:
        for line in fh:
            parsed = json.loads(line.strip())
            assert "action" in parsed


def test_clear_log_removes_file(audit_log):
    log_event("encrypt", "f.env", audit_file=audit_log)
    assert Path(audit_log).exists()
    clear_log(audit_file=audit_log)
    assert not Path(audit_log).exists()


def test_clear_log_noop_when_missing(tmp_path):
    # Should not raise
    clear_log(audit_file=str(tmp_path / "missing.log"))
