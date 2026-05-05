"""Tests for envault.diff."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envault.vault import encrypt_file
from envault.diff import diff_vaults, DiffResult, _parse_env


PASSWORD = "test-secret"


@pytest.fixture()
def old_vault(tmp_path: Path) -> Path:
    env = textwrap.dedent("""\
        DB_HOST=localhost
        DB_PORT=5432
        API_KEY=old-key
        SHARED=same
    """)
    src = tmp_path / ".env"
    src.write_text(env)
    out = tmp_path / "old.env.vault"
    encrypt_file(str(src), PASSWORD, str(out))
    return out


@pytest.fixture()
def new_vault(tmp_path: Path) -> Path:
    env = textwrap.dedent("""\
        DB_HOST=localhost
        API_KEY=new-key
        NEW_VAR=hello
        SHARED=same
    """)
    src = tmp_path / ".env.new"
    src.write_text(env)
    out = tmp_path / "new.env.vault"
    encrypt_file(str(src), PASSWORD, str(out))
    return out


def test_parse_env_basic():
    text = "FOO=bar\nBAZ=qux\n"
    assert _parse_env(text) == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_ignores_comments():
    text = "# comment\nFOO=bar"
    assert _parse_env(text) == {"FOO": "bar"}


def test_parse_env_ignores_blank_lines():
    text = "\nFOO=bar\n\nBAZ=qux\n"
    assert _parse_env(text) == {"FOO": "bar", "BAZ": "qux"}


def test_diff_vaults_returns_diff_result(old_vault, new_vault):
    result = diff_vaults(old_vault, new_vault, PASSWORD)
    assert isinstance(result, DiffResult)


def test_diff_detects_added_keys(old_vault, new_vault):
    result = diff_vaults(old_vault, new_vault, PASSWORD)
    assert "NEW_VAR" in result.added
    assert result.added["NEW_VAR"] == "hello"


def test_diff_detects_removed_keys(old_vault, new_vault):
    result = diff_vaults(old_vault, new_vault, PASSWORD)
    assert "DB_PORT" in result.removed


def test_diff_detects_changed_keys(old_vault, new_vault):
    result = diff_vaults(old_vault, new_vault, PASSWORD)
    assert "API_KEY" in result.changed
    old_val, new_val = result.changed["API_KEY"]
    assert old_val == "old-key"
    assert new_val == "new-key"


def test_diff_detects_unchanged_keys(old_vault, new_vault):
    result = diff_vaults(old_vault, new_vault, PASSWORD)
    assert "SHARED" in result.unchanged
    assert "DB_HOST" in result.unchanged


def test_diff_no_changes_when_same(old_vault):
    result = diff_vaults(old_vault, old_vault, PASSWORD)
    assert not result.added
    assert not result.removed
    assert not result.changed


def test_wrong_password_raises(old_vault, new_vault):
    with pytest.raises(Exception):
        diff_vaults(old_vault, new_vault, "wrong-password")
