"""Tests for envault.history and envault.cli_history."""
from __future__ import annotations

import json
import argparse
from pathlib import Path

import pytest

from envault.audit import clear_log
from envault.history import record_access, get_vault_history, format_history, HistoryEntry
from envault.cli_history import build_history_parser, cmd_history


@pytest.fixture(autouse=True)
def clean_audit(tmp_path, monkeypatch):
    audit_file = tmp_path / "audit.jsonl"
    monkeypatch.setattr("envault.audit.AUDIT_PATH", audit_file, raising=False)
    import envault.audit as _audit
    monkeypatch.setattr(_audit, "_audit_path", lambda: audit_file)
    yield
    clear_log()


@pytest.fixture()
def vault_file(tmp_path):
    v = tmp_path / "secrets.env.vault"
    v.write_bytes(b"dummy")
    return v


def test_record_access_returns_history_entry(vault_file):
    entry = record_access(vault_file, "decrypt", user="alice")
    assert isinstance(entry, HistoryEntry)
    assert entry.action == "decrypt"
    assert entry.user == "alice"
    assert entry.vault == str(vault_file)


def test_record_access_with_note(vault_file):
    entry = record_access(vault_file, "encrypt", user="bob", note="initial setup")
    assert entry.note == "initial setup"


def test_get_vault_history_returns_entries(vault_file):
    record_access(vault_file, "decrypt", user="alice")
    record_access(vault_file, "encrypt", user="bob")
    entries = get_vault_history(vault_file)
    assert len(entries) == 2


def test_get_vault_history_filters_by_vault(tmp_path, vault_file):
    other = tmp_path / "other.vault"
    other.write_bytes(b"x")
    record_access(vault_file, "decrypt", user="alice")
    record_access(other, "decrypt", user="bob")
    entries = get_vault_history(vault_file)
    assert all(e.vault == str(vault_file) for e in entries)
    assert len(entries) == 1


def test_get_vault_history_limit(vault_file):
    for i in range(5):
        record_access(vault_file, "decrypt", user=f"user{i}")
    entries = get_vault_history(vault_file, limit=3)
    assert len(entries) == 3


def test_get_vault_history_empty(vault_file):
    entries = get_vault_history(vault_file)
    assert entries == []


def test_format_history_plain(vault_file):
    record_access(vault_file, "decrypt", user="alice", note="test")
    entries = get_vault_history(vault_file)
    output = format_history(entries, fmt="plain")
    assert "decrypt" in output
    assert "alice" in output
    assert "[test]" in output


def test_format_history_json(vault_file):
    record_access(vault_file, "encrypt", user="bob")
    entries = get_vault_history(vault_file)
    output = format_history(entries, fmt="json")
    data = json.loads(output)
    assert isinstance(data, list)
    assert data[0]["action"] == "encrypt"


def test_format_history_empty():
    assert format_history([]) == "(no history)"


def test_build_history_parser_returns_parser():
    parser = build_history_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_parser_defaults():
    parser = build_history_parser()
    args = parser.parse_args(["my.vault"])
    assert args.vault == "my.vault"
    assert args.limit == 20
    assert args.format == "plain"


def test_cmd_history_missing_vault(tmp_path, capsys):
    parser = build_history_parser()
    args = parser.parse_args([str(tmp_path / "nonexistent.vault")])
    with pytest.raises(SystemExit) as exc:
        cmd_history(args)
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_cmd_history_no_entries(vault_file, capsys):
    parser = build_history_parser()
    args = parser.parse_args([str(vault_file)])
    cmd_history(args)
    captured = capsys.readouterr()
    assert "No history" in captured.out
