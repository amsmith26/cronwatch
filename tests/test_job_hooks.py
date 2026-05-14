"""Tests for cronwatch.job_hooks."""
import pytest

from cronwatch.job_hooks import (
    HookConfig,
    HookResult,
    _run_hook,
    hooks_summary,
    parse_hook_config,
    run_hooks,
)


# ---------------------------------------------------------------------------
# parse_hook_config
# ---------------------------------------------------------------------------

def test_parse_none_returns_empty_config():
    cfg = parse_hook_config(None)
    assert cfg.pre == []
    assert cfg.post_success == []
    assert cfg.post_failure == []


def test_parse_empty_dict_returns_empty_config():
    cfg = parse_hook_config({})
    assert cfg == HookConfig()


def test_parse_string_values_become_lists():
    raw = {"pre": "echo start", "post_success": "echo ok"}
    cfg = parse_hook_config(raw)
    assert cfg.pre == ["echo start"]
    assert cfg.post_success == ["echo ok"]
    assert cfg.post_failure == []


def test_parse_list_values_preserved():
    raw = {"pre": ["echo a", "echo b"], "post_failure": ["echo fail"]}
    cfg = parse_hook_config(raw)
    assert cfg.pre == ["echo a", "echo b"]
    assert cfg.post_failure == ["echo fail"]


# ---------------------------------------------------------------------------
# _run_hook
# ---------------------------------------------------------------------------

def test_run_hook_success():
    result = _run_hook("echo hello")
    assert result.ok
    assert result.returncode == 0
    assert result.stdout == "hello"


def test_run_hook_failure():
    result = _run_hook("exit 1", timeout=5)
    assert not result.ok
    assert result.returncode != 0


def test_run_hook_timeout_returns_minus_one():
    result = _run_hook("sleep 10", timeout=1)
    assert result.returncode == -1
    assert "timeout" in result.stderr


# ---------------------------------------------------------------------------
# run_hooks
# ---------------------------------------------------------------------------

def test_run_hooks_all_succeed():
    results = run_hooks(["echo a", "echo b"])
    assert len(results) == 2
    assert all(r.ok for r in results)


def test_run_hooks_stops_on_first_failure():
    results = run_hooks(["exit 1", "echo should_not_run"])
    assert len(results) == 1
    assert not results[0].ok


def test_run_hooks_empty_list_returns_empty():
    assert run_hooks([]) == []


# ---------------------------------------------------------------------------
# hooks_summary
# ---------------------------------------------------------------------------

def test_hooks_summary_no_hooks():
    assert hooks_summary(HookConfig()) == "no hooks configured"


def test_hooks_summary_lists_sections():
    cfg = HookConfig(pre=["echo start"], post_failure=["echo fail"])
    summary = hooks_summary(cfg)
    assert "pre(1)" in summary
    assert "post_failure(1)" in summary
    assert "post_success" not in summary


def test_hooks_summary_all_sections():
    cfg = HookConfig(
        pre=["echo a"],
        post_success=["echo b", "echo c"],
        post_failure=["echo d"],
    )
    summary = hooks_summary(cfg)
    assert "pre(1)" in summary
    assert "post_success(2)" in summary
    assert "post_failure(1)" in summary
