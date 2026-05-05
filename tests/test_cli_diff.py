"""Tests for envault.cli_diff."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.vault import encrypt_file
from envault.cli_diff import build_diff_parser, cmd_diff


PASSWORD = "cli-diff-secret"


@pytest.fixture()
def env_pair(tmp_path: Path):
    old_src = tmp_path / ".env.old"
    old_src.write_text("FOO=bar\nREMOVED=yes\n")
    old_vault = tmp_path / "old.vault"
    encrypt_file(str(old_src), PASSWORD, str(old_vault))

    new_src = tmp_path / ".env.new"
    new_src.write_text("FOO=bar\nADDED=yes\n")
    new_vault = tmp_path / "new.vault"
    encrypt_file(str(new_src), PASSWORD, str(new_vault))

    return old_vault, new_vault


def test_build_diff_parser_returns_parser():
    parser = build_diff_parser()
    assert parser is not None


def test_parser_requires_old_and_new():
    parser = build_diff_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_parser_separate_passwords_flag():
    parser = build_diff_parser()
    args = parser.parse_args(["old.vault", "new.vault", "--separate-passwords"])
    assert args.separate_passwords is True


def test_parser_separate_passwords_default():
    parser = build_diff_parser()
    args = parser.parse_args(["old.vault", "new.vault"])
    assert args.separate_passwords is False


def test_cmd_diff_shows_added_and_removed(env_pair, capsys):
    old_vault, new_vault = env_pair
    parser = build_diff_parser()
    args = parser.parse_args([str(old_vault), str(new_vault)])

    with patch("envault.cli_diff._prompt", return_value=PASSWORD):
        cmd_diff(args)

    captured = capsys.readouterr()
    assert "+ ADDED" in captured.out
    assert "- REMOVED" in captured.out


def test_cmd_diff_no_changes_message(env_pair, capsys):
    old_vault, _ = env_pair
    parser = build_diff_parser()
    args = parser.parse_args([str(old_vault), str(old_vault)])

    with patch("envault.cli_diff._prompt", return_value=PASSWORD):
        cmd_diff(args)

    captured = capsys.readouterr()
    assert "No differences found" in captured.out


def test_cmd_diff_bad_password_exits(env_pair):
    old_vault, new_vault = env_pair
    parser = build_diff_parser()
    args = parser.parse_args([str(old_vault), str(new_vault)])

    with patch("envault.cli_diff._prompt", return_value="wrong"):
        with pytest.raises(SystemExit) as exc_info:
            cmd_diff(args)
    assert exc_info.value.code == 1
