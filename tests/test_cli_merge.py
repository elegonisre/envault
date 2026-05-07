"""Tests for envault.cli_merge."""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.cli_merge import build_merge_parser, cmd_merge
from envault.vault import encrypt_file

PASSWORD = "cli-merge-pw"


@pytest.fixture()
def vault_pair(tmp_path: Path):
    base_content = "DB_HOST=localhost\nAPP_ENV=prod\n"
    other_content = "DB_HOST=remote\nNEW_VAR=x\n"
    base = tmp_path / "base.vault"
    other = tmp_path / "other.vault"
    encrypt_file(base_content, base, PASSWORD)
    encrypt_file(other_content, other, PASSWORD)
    return base, other, tmp_path


def _make_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    build_merge_parser(sub)
    return root


def test_build_merge_parser_returns_parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    p = build_merge_parser(sub)
    assert isinstance(p, argparse.ArgumentParser)


def test_parser_strategy_default():
    parser = _make_parser()
    args = parser.parse_args(["merge", "a.vault", "b.vault"])
    assert args.strategy == "ours"


def test_parser_strategy_theirs():
    parser = _make_parser()
    args = parser.parse_args(["merge", "a.vault", "b.vault", "--strategy", "theirs"])
    assert args.strategy == "theirs"


def test_parser_separate_passwords_default():
    parser = _make_parser()
    args = parser.parse_args(["merge", "a.vault", "b.vault"])
    assert args.separate_passwords is False


def test_parser_separate_passwords_flag():
    parser = _make_parser()
    args = parser.parse_args(["merge", "a.vault", "b.vault", "--separate-passwords"])
    assert args.separate_passwords is True


def test_cmd_merge_runs(vault_pair, capsys):
    base, other, tmp_path = vault_pair
    output = tmp_path / "out.vault"
    args = argparse.Namespace(
        base=str(base),
        other=str(other),
        output=str(output),
        strategy="ours",
        separate_passwords=False,
    )
    with patch("envault.cli_merge._prompt", return_value=PASSWORD):
        cmd_merge(args)

    captured = capsys.readouterr()
    assert "Merged vault written to" in captured.out
    assert output.exists()


def test_cmd_merge_reports_conflicts(vault_pair, capsys):
    base, other, tmp_path = vault_pair
    output = tmp_path / "out.vault"
    args = argparse.Namespace(
        base=str(base),
        other=str(other),
        output=str(output),
        strategy="ours",
        separate_passwords=False,
    )
    with patch("envault.cli_merge._prompt", return_value=PASSWORD):
        cmd_merge(args)

    captured = capsys.readouterr()
    assert "Conflicts detected" in captured.out
