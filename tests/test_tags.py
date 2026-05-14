"""Tests for envault.tags."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.tags import (
    _tags_path,
    add_tag,
    find_vaults_by_tag,
    read_tags,
    remove_tag,
    write_tags,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "secrets.env.vault"
    p.write_text("placeholder")
    return p


def test_tags_path_has_correct_suffix(vault_file: Path) -> None:
    assert str(_tags_path(vault_file)).endswith(".tags.json")


def test_read_tags_returns_empty_when_no_file(vault_file: Path) -> None:
    assert read_tags(vault_file) == []


def test_write_tags_creates_file(vault_file: Path) -> None:
    write_tags(vault_file, ["production", "backend"])
    assert _tags_path(vault_file).exists()


def test_write_tags_persists_sorted_unique(vault_file: Path) -> None:
    write_tags(vault_file, ["beta", "alpha", "beta"])
    data = json.loads(_tags_path(vault_file).read_text())
    assert data["tags"] == ["alpha", "beta"]


def test_read_tags_returns_written_tags(vault_file: Path) -> None:
    write_tags(vault_file, ["staging", "frontend"])
    assert read_tags(vault_file) == ["frontend", "staging"]


def test_write_tags_raises_on_invalid_tag(vault_file: Path) -> None:
    with pytest.raises(ValueError, match="Invalid tag"):
        write_tags(vault_file, ["UPPER_CASE"])


def test_write_tags_raises_on_spaces(vault_file: Path) -> None:
    with pytest.raises(ValueError):
        write_tags(vault_file, ["has space"])


def test_add_tag_adds_new_tag(vault_file: Path) -> None:
    add_tag(vault_file, "production")
    assert "production" in read_tags(vault_file)


def test_add_tag_is_idempotent(vault_file: Path) -> None:
    add_tag(vault_file, "production")
    add_tag(vault_file, "production")
    assert read_tags(vault_file).count("production") == 1


def test_remove_tag_removes_existing_tag(vault_file: Path) -> None:
    write_tags(vault_file, ["alpha", "beta"])
    remaining = remove_tag(vault_file, "alpha")
    assert remaining == ["beta"]
    assert "alpha" not in read_tags(vault_file)


def test_remove_tag_noop_when_absent(vault_file: Path) -> None:
    write_tags(vault_file, ["beta"])
    result = remove_tag(vault_file, "nonexistent")
    assert result == ["beta"]


def test_find_vaults_by_tag(tmp_path: Path) -> None:
    v1 = tmp_path / "a.vault"
    v2 = tmp_path / "b.vault"
    v1.write_text("x")
    v2.write_text("x")
    write_tags(v1, ["production"])
    write_tags(v2, ["staging"])
    results = find_vaults_by_tag(tmp_path, "production")
    assert v1 in results
    assert v2 not in results


def test_find_vaults_by_tag_empty_when_none_match(tmp_path: Path) -> None:
    v = tmp_path / "c.vault"
    v.write_text("x")
    write_tags(v, ["dev"])
    assert find_vaults_by_tag(tmp_path, "production") == []
