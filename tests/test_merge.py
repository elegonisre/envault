"""Tests for envault.merge."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envault.merge import MergeResult, _dict_to_env, _parse_env, merge_vaults
from envault.vault import encrypt_file, decrypt_file

PASSWORD = "test-secret"


@pytest.fixture()
def base_vault(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        DB_HOST=localhost
        DB_PORT=5432
        APP_ENV=production
    """)
    p = tmp_path / "base.vault"
    encrypt_file(content, p, PASSWORD)
    return p


@pytest.fixture()
def other_vault(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        DB_HOST=remotehost
        DB_PORT=5432
        NEW_KEY=hello
    """)
    p = tmp_path / "other.vault"
    encrypt_file(content, p, PASSWORD)
    return p


def test_parse_env_basic():
    text = "KEY=value\nOTHER=123\n"
    assert _parse_env(text) == {"KEY": "value", "OTHER": "123"}


def test_parse_env_skips_comments():
    text = "# comment\nKEY=value\n"
    assert _parse_env(text) == {"KEY": "value"}


def test_parse_env_skips_blank_lines():
    text = "\nKEY=value\n\n"
    assert _parse_env(text) == {"KEY": "value"}


def test_dict_to_env_sorted():
    data = {"Z": "1", "A": "2"}
    lines = _dict_to_env(data).splitlines()
    assert lines[0].startswith("A=")
    assert lines[1].startswith("Z=")


def test_merge_adds_new_keys(base_vault: Path, other_vault: Path, tmp_path: Path):
    out = tmp_path / "merged.vault"
    result = merge_vaults(base_vault, other_vault, PASSWORD, PASSWORD, out, PASSWORD)
    assert "NEW_KEY" in result.added
    assert "NEW_KEY" in result.merged


def test_merge_detects_conflicts(base_vault: Path, other_vault: Path, tmp_path: Path):
    out = tmp_path / "merged.vault"
    result = merge_vaults(base_vault, other_vault, PASSWORD, PASSWORD, out, PASSWORD)
    assert "DB_HOST" in result.conflicts


def test_merge_strategy_ours_keeps_base(base_vault: Path, other_vault: Path, tmp_path: Path):
    out = tmp_path / "merged.vault"
    result = merge_vaults(base_vault, other_vault, PASSWORD, PASSWORD, out, PASSWORD, strategy="ours")
    assert result.merged["DB_HOST"] == "localhost"
    assert result.overwritten == []


def test_merge_strategy_theirs_overwrites(base_vault: Path, other_vault: Path, tmp_path: Path):
    out = tmp_path / "merged.vault"
    result = merge_vaults(base_vault, other_vault, PASSWORD, PASSWORD, out, PASSWORD, strategy="theirs")
    assert result.merged["DB_HOST"] == "remotehost"
    assert "DB_HOST" in result.overwritten


def test_merge_output_is_decryptable(base_vault: Path, other_vault: Path, tmp_path: Path):
    out = tmp_path / "merged.vault"
    merge_vaults(base_vault, other_vault, PASSWORD, PASSWORD, out, PASSWORD)
    text = decrypt_file(out, PASSWORD)
    assert "NEW_KEY=hello" in text


def test_merge_invalid_strategy_raises(base_vault: Path, other_vault: Path, tmp_path: Path):
    out = tmp_path / "merged.vault"
    with pytest.raises(ValueError, match="Unknown merge strategy"):
        merge_vaults(base_vault, other_vault, PASSWORD, PASSWORD, out, PASSWORD, strategy="bad")


def test_merge_returns_merge_result(base_vault: Path, other_vault: Path, tmp_path: Path):
    out = tmp_path / "merged.vault"
    result = merge_vaults(base_vault, other_vault, PASSWORD, PASSWORD, out, PASSWORD)
    assert isinstance(result, MergeResult)
