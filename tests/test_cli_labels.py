"""Tests for cronwatch.cli_labels."""

from __future__ import annotations

import argparse
import types

import pytest

from cronwatch.cli_labels import (
    _cmd_index,
    _cmd_list,
    _cmd_show,
    add_labels_subparser,
    cmd_labels,
)


class _FakeJob:
    def __init__(self, name, labels=None):
        self.name = name
        self.labels = labels


@pytest.fixture()
def cfg():
    c = types.SimpleNamespace()
    c.jobs = [
        _FakeJob("backup", {"env": "prod", "team": "ops"}),
        _FakeJob("report", {"env": "prod", "team": "data"}),
        _FakeJob("cleanup", {"env": "staging"}),
    ]
    return c


@pytest.fixture()
def empty_cfg():
    c = types.SimpleNamespace()
    c.jobs = []
    return c


def test_add_labels_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_labels_subparser(sub)
    ns = parser.parse_args(["labels", "list"])
    assert ns.command == "labels"


def test_cmd_list_prints_keys(cfg, capsys):
    args = argparse.Namespace()
    rc = _cmd_list(args, cfg)
    out = capsys.readouterr().out
    assert "env" in out
    assert "team" in out
    assert rc == 0


def test_cmd_list_empty(empty_cfg, capsys):
    args = argparse.Namespace()
    rc = _cmd_list(args, empty_cfg)
    out = capsys.readouterr().out
    assert "no labels" in out
    assert rc == 0


def test_cmd_show_with_value(cfg, capsys):
    args = argparse.Namespace(key="env", value="prod")
    rc = _cmd_show(args, cfg)
    out = capsys.readouterr().out
    assert "backup" in out
    assert "report" in out
    assert "cleanup" not in out
    assert rc == 0


def test_cmd_show_no_match(cfg, capsys):
    args = argparse.Namespace(key="env", value="unknown")
    rc = _cmd_show(args, cfg)
    out = capsys.readouterr().out
    assert "no jobs match" in out
    assert rc == 0


def test_cmd_index_output(cfg, capsys):
    args = argparse.Namespace()
    rc = _cmd_index(args, cfg)
    out = capsys.readouterr().out
    assert "env=prod" in out
    assert "team=ops" in out
    assert rc == 0


def test_cmd_labels_no_subcommand_returns_nonzero(cfg, capsys):
    args = argparse.Namespace()
    rc = cmd_labels(args, cfg)
    assert rc == 1
