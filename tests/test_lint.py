"""Tests for envault.lint and envault.cli_lint."""
from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.lint import LintIssue, LintResult, _check_line, lint_vault
from envault.cli_lint import build_lint_parser, cmd_lint
from envault.vault import encrypt_file


# ---------------------------------------------------------------------------
# _check_line unit tests
# ---------------------------------------------------------------------------

def test_blank_line_no_issues():
    assert _check_line(1, '') == []


def test_comment_no_issues():
    assert _check_line(1, '# comment') == []


def test_missing_equals_is_error():
    issues = _check_line(1, 'BADLINE')
    assert any(i.severity == 'error' and 'separator' in i.message for i in issues)


def test_lowercase_key_is_warning():
    issues = _check_line(1, 'my_key=value')
    assert any(i.severity == 'warning' and 'UPPER_SNAKE_CASE' in i.message for i in issues)


def test_empty_value_is_warning():
    issues = _check_line(1, 'MY_KEY=')
    assert any(i.severity == 'warning' and 'empty' in i.message for i in issues)


def test_unquoted_whitespace_is_error():
    issues = _check_line(1, 'MY_KEY=hello world')
    assert any(i.severity == 'error' and 'whitespace' in i.message for i in issues)


def test_unnecessary_quotes_is_warning():
    issues = _check_line(1, 'MY_KEY="simplevalue"')
    assert any(i.severity == 'warning' and 'quoted' in i.message for i in issues)


def test_clean_line_no_issues():
    assert _check_line(1, 'MY_KEY=simplevalue') == []


# ---------------------------------------------------------------------------
# lint_vault integration tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_file(tmp_path: Path):
    env_content = textwrap.dedent("""\
        DATABASE_URL=postgres://localhost/db
        SECRET_KEY=abc123
        bad_key=oops
        MISSING_VALUE=
    """)
    src = tmp_path / '.env'
    src.write_text(env_content)
    vault = tmp_path / '.env.vault'
    encrypt_file(src, vault, 'testpass')
    return vault


def test_lint_vault_returns_lint_result(vault_file):
    result = lint_vault(vault_file, 'testpass')
    assert isinstance(result, LintResult)


def test_lint_vault_detects_lowercase_key(vault_file):
    result = lint_vault(vault_file, 'testpass')
    keys = [i.key for i in result.issues]
    assert 'bad_key' in keys


def test_lint_vault_detects_empty_value(vault_file):
    result = lint_vault(vault_file, 'testpass')
    assert any(i.key == 'MISSING_VALUE' for i in result.issues)


def test_lint_vault_ok_property_false_when_errors(tmp_path):
    src = tmp_path / '.env'
    src.write_text('BADLINE\n')
    vault = tmp_path / '.env.vault'
    encrypt_file(src, vault, 'pw')
    result = lint_vault(vault, 'pw')
    assert not result.ok


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_build_lint_parser_returns_parser():
    parser = build_lint_parser()
    assert parser is not None


def test_cmd_lint_missing_file(tmp_path, capsys):
    args = build_lint_parser().parse_args(['nonexistent.vault', '--password', 'pw'])
    rc = cmd_lint(args)
    assert rc == 1
    assert 'not found' in capsys.readouterr().err


def test_cmd_lint_clean_vault(tmp_path):
    src = tmp_path / '.env'
    src.write_text('MY_KEY=cleanvalue\nANOTHER=123\n')
    vault = tmp_path / '.env.vault'
    encrypt_file(src, vault, 'pw')
    args = build_lint_parser().parse_args([str(vault), '--password', 'pw'])
    rc = cmd_lint(args)
    assert rc == 0


def test_cmd_lint_wrong_password(vault_file, capsys):
    args = build_lint_parser().parse_args([str(vault_file), '--password', 'wrongpass'])
    rc = cmd_lint(args)
    assert rc == 1
    assert 'decrypt' in capsys.readouterr().err
