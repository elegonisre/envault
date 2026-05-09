"""Tests for envault.compare and envault.cli_compare."""

from __future__ import annotations

import pytest

from envault.vault import encrypt_file
from envault.compare import CompareResult, _parse_env, compare_vaults
from envault.cli_compare import build_compare_parser, cmd_compare


PASSWORD = "test-secret"


@pytest.fixture()
def vault_pair(tmp_path):
    old_env = "KEY_A=alpha\nKEY_B=beta\nSHARED=same\n"
    new_env = "KEY_B=changed\nSHARED=same\nKEY_C=gamma\n"

    old_path = str(tmp_path / "old.env.vault")
    new_path = str(tmp_path / "new.env.vault")

    old_src = tmp_path / "old.env"
    new_src = tmp_path / "new.env"
    old_src.write_text(old_env)
    new_src.write_text(new_env)

    encrypt_file(str(old_src), PASSWORD, output=old_path)
    encrypt_file(str(new_src), PASSWORD, output=new_path)

    return old_path, new_path


# --- _parse_env ---

def test_parse_env_basic():
    text = "FOO=bar\nBAZ=qux\n"
    assert _parse_env(text) == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_ignores_comments():
    text = "# comment\nFOO=bar\n"
    assert _parse_env(text) == {"FOO": "bar"}


def test_parse_env_ignores_blank_lines():
    text = "\nFOO=bar\n\n"
    assert _parse_env(text) == {"FOO": "bar"}


def test_parse_env_handles_equals_in_value():
    text = "FOO=bar=baz\n"
    assert _parse_env(text) == {"FOO": "bar=baz"}


# --- compare_vaults ---

def test_compare_returns_compare_result(vault_pair):
    old, new = vault_pair
    result = compare_vaults(old, new, PASSWORD)
    assert isinstance(result, CompareResult)


def test_only_in_old(vault_pair):
    old, new = vault_pair
    result = compare_vaults(old, new, PASSWORD)
    assert "KEY_A" in result.only_in_old


def test_only_in_new(vault_pair):
    old, new = vault_pair
    result = compare_vaults(old, new, PASSWORD)
    assert "KEY_C" in result.only_in_new


def test_changed_key(vault_pair):
    old, new = vault_pair
    result = compare_vaults(old, new, PASSWORD)
    assert "KEY_B" in result.changed


def test_unchanged_key(vault_pair):
    old, new = vault_pair
    result = compare_vaults(old, new, PASSWORD)
    assert "SHARED" in result.unchanged


def test_has_differences_true(vault_pair):
    old, new = vault_pair
    result = compare_vaults(old, new, PASSWORD)
    assert result.has_differences is True


def test_has_differences_false(vault_pair):
    old, _ = vault_pair
    result = compare_vaults(old, old, PASSWORD)
    assert result.has_differences is False


def test_separate_passwords_accepted(vault_pair):
    old, new = vault_pair
    result = compare_vaults(old, new, PASSWORD, new_password=PASSWORD)
    assert isinstance(result, CompareResult)


# --- CLI ---

def test_build_compare_parser_returns_parser():
    parser = build_compare_parser()
    assert parser is not None


def test_parser_requires_old_and_new():
    parser = build_compare_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_parser_separate_passwords_default():
    parser = build_compare_parser()
    args = parser.parse_args(["old.vault", "new.vault"])
    assert args.separate_passwords is False


def test_parser_show_unchanged_default():
    parser = build_compare_parser()
    args = parser.parse_args(["old.vault", "new.vault"])
    assert args.show_unchanged is False


def test_cmd_compare_identical_vaults(vault_pair, monkeypatch, capsys):
    old, _ = vault_pair
    monkeypatch.setattr("envault.cli_compare._prompt", lambda _: PASSWORD)
    parser = build_compare_parser()
    args = parser.parse_args([old, old])
    cmd_compare(args)
    captured = capsys.readouterr()
    assert "identical" in captured.out
