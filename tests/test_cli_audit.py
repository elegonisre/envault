"""Tests for envault.cli_audit module."""

import argparse
import json
import pytest

from envault.audit import log_event
from envault.cli_audit import build_audit_parser, cmd_log


@pytest.fixture()
def audit_log(tmp_path):
    path = str(tmp_path / "audit.log")
    for action, target in [("encrypt", "a.env"), ("decrypt", "b.vault"), ("share", "c.env")]:
        log_event(action, target, user="bob", audit_file=path)
    return path


def _run(args_list, audit_log):
    parser = build_audit_parser()
    args = parser.parse_args(args_list + ["--audit-file", audit_log])
    return args


def test_build_audit_parser_returns_parser():
    parser = build_audit_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_parser_defaults(audit_log):
    args = _run([], audit_log)
    assert args.last == 0
    assert args.json is False


def test_cmd_log_plain_output(audit_log, capsys):
    args = _run([], audit_log)
    cmd_log(args)
    out = capsys.readouterr().out
    assert "encrypt" in out.lower()
    assert "bob" in out


def test_cmd_log_json_output(audit_log, capsys):
    args = _run(["--json"], audit_log)
    cmd_log(args)
    out = capsys.readouterr().out
    entries = json.loads(out)
    assert isinstance(entries, list)
    assert len(entries) == 3


def test_cmd_log_last_n(audit_log, capsys):
    args = _run(["--last", "2"], audit_log)
    cmd_log(args)
    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if l.strip()]
    assert len(lines) == 2


def test_cmd_log_empty_log(tmp_path, capsys):
    empty = str(tmp_path / "empty.log")
    args = _run([], empty)
    cmd_log(args)
    err = capsys.readouterr().err
    assert "No audit entries" in err


def test_build_audit_parser_as_subparser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    build_audit_parser(parent=sub)
    args = root.parse_args(["log"])
    assert hasattr(args, "func")
