"""Tests for cronwatch.job_quota and cronwatch.quota_config."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from cronwatch.job_quota import JobQuota, QuotaRule
from cronwatch.quota_config import parse_quota_rule, build_quota_from_config


@pytest.fixture
def quota() -> JobQuota:
    q = JobQuota()
    q.register("backup", QuotaRule(max_runs=3, window_seconds=60))
    return q


def test_unregistered_job_is_always_allowed(quota: JobQuota) -> None:
    assert quota.is_allowed("unknown-job") is True


def test_first_run_is_allowed(quota: JobQuota) -> None:
    assert quota.is_allowed("backup") is True


def test_runs_up_to_max_are_allowed(quota: JobQuota) -> None:
    for _ in range(3):
        assert quota.is_allowed("backup") is True
        quota.record_run("backup")


def test_exceeding_max_is_denied(quota: JobQuota) -> None:
    for _ in range(3):
        quota.record_run("backup")
    assert quota.is_allowed("backup") is False


def test_runs_in_window_counts_correctly(quota: JobQuota) -> None:
    quota.record_run("backup")
    quota.record_run("backup")
    assert quota.runs_in_window("backup") == 2


def test_remaining_decreases_with_runs(quota: JobQuota) -> None:
    assert quota.remaining("backup") == 3
    quota.record_run("backup")
    assert quota.remaining("backup") == 2


def test_remaining_is_none_for_unregistered(quota: JobQuota) -> None:
    assert quota.remaining("no-rule") is None


def test_old_runs_pruned_after_window(quota: JobQuota) -> None:
    base = time.time()
    with patch("time.time", return_value=base - 120):
        for _ in range(3):
            quota.record_run("backup")
    # Now all timestamps are outside the 60-second window
    assert quota.is_allowed("backup") is True


def test_parse_quota_rule_none_returns_none() -> None:
    assert parse_quota_rule(None) is None


def test_parse_quota_rule_missing_max_runs_returns_none() -> None:
    assert parse_quota_rule({"window_size": 1, "window_unit": "hours"}) is None


def test_parse_quota_rule_basic() -> None:
    rule = parse_quota_rule({"max_runs": 5, "window_size": 2, "window_unit": "hours"})
    assert rule is not None
    assert rule.max_runs == 5
    assert rule.window_seconds == pytest.approx(7200)


def test_parse_quota_rule_minutes() -> None:
    rule = parse_quota_rule({"max_runs": 10, "window_size": 30, "window_unit": "minutes"})
    assert rule is not None
    assert rule.window_seconds == pytest.approx(1800)


def test_parse_quota_rule_string_integers_coerced() -> None:
    rule = parse_quota_rule({"max_runs": "4", "window_size": "1", "window_unit": "days"})
    assert rule is not None
    assert rule.max_runs == 4
    assert rule.window_seconds == pytest.approx(86400)


def test_build_quota_from_config_registers_jobs() -> None:
    class FakeJob:
        def __init__(self, name, quota):
            self.name = name
            self.quota = quota

    jobs = [
        FakeJob("job-a", {"max_runs": 2, "window_size": 1, "window_unit": "hours"}),
        FakeJob("job-b", None),
    ]
    q = build_quota_from_config(jobs)
    assert q.remaining("job-a") == 2
    assert q.remaining("job-b") is None
