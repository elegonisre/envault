"""Tests for envault.pin — vault pinning to snapshots."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import encrypt_file
from envault.snapshot import save_snapshot
from envault.pin import set_pin, get_pin, clear_pin, restore_pinned, _pin_path


PASSWORD = "pintest"
ENV_CONTENT = "API_KEY=abc123\nDEBUG=true\n"


@pytest.fixture()
def vault_file(tmp_path):
    env = tmp_path / "test.env"
    env.write_text(ENV_CONTENT)
    vault = tmp_path / "test.env.vault"
    encrypt_file(str(env), PASSWORD, str(vault))
    return vault


@pytest.fixture()
def snapshot_id(vault_file):
    meta = save_snapshot(vault_file, PASSWORD, note="initial")
    return meta["id"]


def test_pin_path_has_correct_suffix(vault_file):
    p = _pin_path(vault_file)
    assert p.name.endswith(".vault.pin")


def test_get_pin_returns_none_when_no_pin(vault_file):
    assert get_pin(vault_file) is None


def test_set_pin_creates_file(vault_file, snapshot_id):
    set_pin(vault_file, snapshot_id)
    assert _pin_path(vault_file).exists()


def test_set_pin_returns_dict(vault_file, snapshot_id):
    pin = set_pin(vault_file, snapshot_id)
    assert isinstance(pin, dict)
    assert pin["pinned_to"] == snapshot_id


def test_get_pin_returns_record_after_set(vault_file, snapshot_id):
    set_pin(vault_file, snapshot_id)
    pin = get_pin(vault_file)
    assert pin is not None
    assert pin["pinned_to"] == snapshot_id


def test_set_pin_raises_for_unknown_snapshot(vault_file):
    with pytest.raises(ValueError, match="not found"):
        set_pin(vault_file, "nonexistent-id-0000")


def test_clear_pin_removes_file(vault_file, snapshot_id):
    set_pin(vault_file, snapshot_id)
    result = clear_pin(vault_file)
    assert result is True
    assert not _pin_path(vault_file).exists()


def test_clear_pin_returns_false_when_no_pin(vault_file):
    result = clear_pin(vault_file)
    assert result is False


def test_restore_pinned_returns_none_when_unpinned(vault_file):
    result = restore_pinned(vault_file, PASSWORD)
    assert result is None


def test_restore_pinned_returns_snapshot_id(vault_file, snapshot_id):
    set_pin(vault_file, snapshot_id)
    restored = restore_pinned(vault_file, PASSWORD)
    assert restored == snapshot_id


def test_restore_pinned_vault_is_readable(vault_file, snapshot_id, tmp_path):
    from envault.vault import decrypt_file

    set_pin(vault_file, snapshot_id)
    restore_pinned(vault_file, PASSWORD)
    out = tmp_path / "restored.env"
    decrypt_file(str(vault_file), PASSWORD, str(out))
    assert "API_KEY" in out.read_text()
