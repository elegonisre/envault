"""Tests for envault.export and envault.cli_export."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.vault import encrypt_file
from envault.export import export_vault, _parse_env
from envault.cli_export import build_export_parser, cmd_export


ENV_CONTENT = 'DB_HOST=localhost\nDB_PORT=5432\n# comment\nSECRET_KEY=abc123\n'
PASSWORD = "test-password"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT)
    vault = tmp_path / ".env.vault"
    encrypt_file(env, PASSWORD, vault)
    return vault


# --- _parse_env ---

def test_parse_env_basic():
    pairs = _parse_env("FOO=bar\nBAZ=qux\n")
    assert pairs == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_ignores_comments():
    pairs = _parse_env("# comment\nFOO=bar\n")
    assert "#" not in str(pairs)


def test_parse_env_strips_quotes():
    pairs = _parse_env('KEY="value"\n')
    assert pairs["KEY"] == "value"


# --- export_vault ---

def test_export_dotenv_format(vault_file: Path):
    result = export_vault(vault_file, PASSWORD, fmt="dotenv")
    assert 'DB_HOST="localhost"' in result
    assert 'SECRET_KEY="abc123"' in result


def test_export_json_format(vault_file: Path):
    result = export_vault(vault_file, PASSWORD, fmt="json")
    data = json.loads(result)
    assert data["DB_HOST"] == "localhost"
    assert data["SECRET_KEY"] == "abc123"


def test_export_shell_format(vault_file: Path):
    result = export_vault(vault_file, PASSWORD, fmt="shell")
    assert "export DB_HOST='localhost'" in result
    assert "export SECRET_KEY='abc123'" in result


def test_export_writes_file(vault_file: Path, tmp_path: Path):
    out = tmp_path / "exported.json"
    export_vault(vault_file, PASSWORD, fmt="json", output_path=out)
    assert out.exists()
    data = json.loads(out.read_text())
    assert "DB_HOST" in data


def test_export_unknown_format_raises(vault_file: Path):
    with pytest.raises(ValueError, match="Unknown export format"):
        export_vault(vault_file, PASSWORD, fmt="xml")  # type: ignore[arg-type]


def test_export_wrong_password_raises(vault_file: Path):
    with pytest.raises(Exception):
        export_vault(vault_file, "wrong-password")


# --- CLI ---

def test_build_export_parser_returns_parser():
    parser = build_export_parser()
    assert parser is not None


def test_parser_format_choices():
    parser = build_export_parser()
    args = parser.parse_args(["some.vault", "--format", "json"])
    assert args.format == "json"


def test_parser_default_format():
    parser = build_export_parser()
    args = parser.parse_args(["some.vault"])
    assert args.format == "dotenv"


def test_cmd_export_stdout(vault_file: Path, capsys):
    parser = build_export_parser()
    args = parser.parse_args([str(vault_file), "--password", PASSWORD, "--format", "json"])
    cmd_export(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["DB_HOST"] == "localhost"


def test_cmd_export_to_file(vault_file: Path, tmp_path: Path, capsys):
    out = tmp_path / "out.env"
    parser = build_export_parser()
    args = parser.parse_args([
        str(vault_file), "--password", PASSWORD, "--output", str(out),
    ])
    cmd_export(args)
    assert out.exists()
    assert "DB_HOST" in out.read_text()
