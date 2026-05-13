"""Tests for cronwatch.job_env."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from cronwatch.job_env import base_env, build_job_env, redact_env


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

class _FakeJob:
    """Minimal stand-in for JobConfig."""
    def __init__(self, env=None, name="test_job", schedule="@hourly", command="echo hi"):
        self.env = env
        self.name = name
        self.schedule = schedule
        self.command = command


# ---------------------------------------------------------------------------
# base_env
# ---------------------------------------------------------------------------

def test_base_env_returns_dict():
    env = base_env()
    assert isinstance(env, dict)


def test_base_env_is_copy():
    env = base_env()
    env["__CRONWATCH_TEST__"] = "1"
    assert "__CRONWATCH_TEST__" not in os.environ


# ---------------------------------------------------------------------------
# build_job_env
# ---------------------------------------------------------------------------

def test_build_job_env_inherits_process_env():
    with patch.dict(os.environ, {"CRONWATCH_MARKER": "yes"}):
        env = build_job_env(_FakeJob())
    assert env["CRONWATCH_MARKER"] == "yes"


def test_build_job_env_applies_job_overrides():
    job = _FakeJob(env={"MY_VAR": "hello"})
    env = build_job_env(job, inherit=False)
    assert env["MY_VAR"] == "hello"


def test_build_job_env_extra_has_highest_priority():
    job = _FakeJob(env={"PRIORITY": "job"})
    env = build_job_env(job, extra={"PRIORITY": "extra"}, inherit=False)
    assert env["PRIORITY"] == "extra"


def test_build_job_env_no_inherit_empty_base():
    job = _FakeJob(env={"ONLY": "this"})
    env = build_job_env(job, inherit=False)
    # Should not contain arbitrary process variables
    # (PATH might be set by the job env explicitly — it isn't here)
    assert set(env.keys()) == {"ONLY"}


def test_build_job_env_none_env_is_ok():
    job = _FakeJob(env=None)
    env = build_job_env(job, inherit=False)
    assert isinstance(env, dict)


# ---------------------------------------------------------------------------
# redact_env
# ---------------------------------------------------------------------------

def test_redact_env_hides_password():
    env = {"DB_PASSWORD": "s3cr3t", "HOST": "localhost"}
    result = redact_env(env)
    assert result["DB_PASSWORD"] == "***"
    assert result["HOST"] == "localhost"


def test_redact_env_custom_keys():
    env = {"MY_BANANA": "yellow", "OTHER": "fine"}
    result = redact_env(env, sensitive_keys=["banana"])
    assert result["MY_BANANA"] == "***"
    assert result["OTHER"] == "fine"


def test_redact_env_does_not_mutate_original():
    env = {"API_TOKEN": "abc123"}
    redact_env(env)
    assert env["API_TOKEN"] == "abc123"


def test_redact_env_case_insensitive_key_matching():
    env = {"MYSECRETKEY": "val"}
    result = redact_env(env)
    assert result["MYSECRETKEY"] == "***"
