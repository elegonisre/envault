"""Tests for envault.search and envault.cli_search."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault.vault import encrypt_file
from envault.search import search_vault, search_vaults, SearchResult
from envault.cli_search import build_search_parser, cmd_search

PASSWORD = "hunter2"

ENV_CONTENT = """# sample env
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=supersecret
API_KEY=abc123
DEBUG=true
"""


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT)
    out = tmp_path / ".env.vault"
    encrypt_file(env, PASSWORD, output_path=out)
    return out


@pytest.fixture()
def two_vaults(tmp_path: Path):
    paths = []
    for name, content in [
        ("a.vault", "FOO=1\nBAR=2\n"),
        ("b.vault", "FOO=3\nBAZ=4\n"),
    ]:
        env = tmp_path / (name + ".env")
        env.write_text(content)
        out = tmp_path / name
        encrypt_file(env, PASSWORD, output_path=out)
        paths.append(out)
    return paths


def test_search_vault_returns_list(vault_file):
    results = search_vault(vault_file, PASSWORD, "DB_")
    assert isinstance(results, list)


def test_search_vault_finds_matching_keys(vault_file):
    results = search_vault(vault_file, PASSWORD, "DB_")
    keys = [r.key for r in results]
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys


def test_search_vault_excludes_non_matching(vault_file):
    results = search_vault(vault_file, PASSWORD, "DB_")
    keys = [r.key for r in results]
    assert "SECRET_KEY" not in keys


def test_search_result_has_line_number(vault_file):
    results = search_vault(vault_file, PASSWORD, "SECRET_KEY")
    assert len(results) == 1
    assert results[0].line_number > 0


def test_search_vault_ignore_case(vault_file):
    results = search_vault(vault_file, PASSWORD, "db_host", ignore_case=True)
    assert len(results) == 1
    assert results[0].key == "DB_HOST"


def test_search_vault_values(vault_file):
    results = search_vault(vault_file, PASSWORD, "supersecret", search_values=True)
    assert len(results) == 1
    assert results[0].key == "SECRET_KEY"


def test_search_vaults_aggregates(two_vaults):
    results = search_vaults(two_vaults, PASSWORD, "FOO")
    assert len(results) == 2


def test_build_search_parser_returns_parser():
    p = build_search_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_parser_pattern_and_vaults(vault_file):
    p = build_search_parser()
    args = p.parse_args(["DB_", str(vault_file)])
    assert args.pattern == "DB_"
    assert args.vaults == [str(vault_file)]


def test_parser_defaults(vault_file):
    p = build_search_parser()
    args = p.parse_args(["X", str(vault_file)])
    assert args.values is False
    assert args.show_values is False
    assert args.ignore_case is False


def test_cmd_search_prints_matches(vault_file, capsys):
    p = build_search_parser()
    args = p.parse_args(["DB_", str(vault_file)])
    cmd_search(args, password=PASSWORD)
    captured = capsys.readouterr()
    assert "DB_HOST" in captured.out
    assert "DB_PORT" in captured.out


def test_cmd_search_no_matches_message(vault_file, capsys):
    p = build_search_parser()
    args = p.parse_args(["NONEXISTENT_KEY", str(vault_file)])
    cmd_search(args, password=PASSWORD)
    captured = capsys.readouterr()
    assert "No matches found" in captured.out
