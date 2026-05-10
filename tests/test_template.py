"""Tests for envault.template — vault-driven template rendering."""

from __future__ import annotations

import pytest

from envault.template import RenderResult, _parse_env, render_template
from envault.vault import encrypt_file


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_file(tmp_path):
    """Encrypted vault with a handful of variables."""
    env_content = "DB_HOST=localhost\nDB_PORT=5432\nSECRET=s3cr3t\n"
    env_path = tmp_path / "sample.env"
    env_path.write_text(env_content)
    vault_path = tmp_path / "sample.env.vault"
    encrypt_file(env_path, "password123", vault_path)
    return vault_path


@pytest.fixture()
def template_file(tmp_path):
    content = "host=${DB_HOST} port=${DB_PORT} secret=$SECRET unknown=${MISSING}\n"
    p = tmp_path / "config.tmpl"
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# _parse_env unit tests
# ---------------------------------------------------------------------------

def test_parse_env_basic():
    result = _parse_env("FOO=bar\nBAZ=qux\n")
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_strips_quotes():
    result = _parse_env('KEY="hello world"\n')
    assert result["KEY"] == "hello world"


def test_parse_env_ignores_comments():
    result = _parse_env("# comment\nFOO=1\n")
    assert "#" not in "".join(result.keys())
    assert result["FOO"] == "1"


def test_parse_env_ignores_blank_lines():
    result = _parse_env("\n\nFOO=bar\n\n")
    assert list(result.keys()) == ["FOO"]


# ---------------------------------------------------------------------------
# render_template integration tests
# ---------------------------------------------------------------------------

def test_render_template_returns_render_result(vault_file, template_file):
    result = render_template(template_file, vault_file, "password123")
    assert isinstance(result, RenderResult)


def test_render_template_substitutes_braced_vars(vault_file, template_file):
    result = render_template(template_file, vault_file, "password123")
    assert "localhost" in result.output
    assert "5432" in result.output


def test_render_template_substitutes_bare_dollar_var(vault_file, template_file):
    result = render_template(template_file, vault_file, "password123")
    assert "s3cr3t" in result.output


def test_render_template_tracks_substitution_count(vault_file, template_file):
    result = render_template(template_file, vault_file, "password123")
    assert result.substituted == 3  # DB_HOST, DB_PORT, SECRET


def test_render_template_reports_missing_keys(vault_file, template_file):
    result = render_template(template_file, vault_file, "password123")
    assert "MISSING" in result.missing_keys


def test_render_template_leaves_missing_placeholder_unchanged(vault_file, template_file):
    result = render_template(template_file, vault_file, "password123")
    assert "${MISSING}" in result.output


def test_render_template_strict_raises_on_missing(vault_file, template_file):
    with pytest.raises(KeyError, match="MISSING"):
        render_template(template_file, vault_file, "password123", strict=True)


def test_render_template_writes_output_file(vault_file, template_file, tmp_path):
    out = tmp_path / "rendered.conf"
    render_template(template_file, vault_file, "password123", output_path=out)
    assert out.exists()
    assert "localhost" in out.read_text()


def test_render_template_wrong_password_raises(vault_file, template_file):
    with pytest.raises(Exception):
        render_template(template_file, vault_file, "wrongpassword")
