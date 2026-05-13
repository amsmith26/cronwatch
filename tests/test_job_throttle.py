"""Tests for cronwatch.job_throttle."""

import pytest
from cronwatch.job_throttle import JobThrottle, ThrottleRule, parse_throttle_rules

BASE = 1_000_000.0


@pytest.fixture
def throttle() -> JobThrottle:
    t = JobThrottle()
    t.register("backup", ThrottleRule(min_interval_seconds=300))
    return t


def test_unregistered_job_is_never_throttled(throttle):
    assert throttle.is_throttled("unknown_job", now=BASE) is False


def test_first_run_is_not_throttled(throttle):
    assert throttle.is_throttled("backup", now=BASE) is False


def test_throttled_immediately_after_run(throttle):
    throttle.record_run("backup", now=BASE)
    assert throttle.is_throttled("backup", now=BASE + 1) is True


def test_not_throttled_after_interval_expires(throttle):
    throttle.record_run("backup", now=BASE)
    assert throttle.is_throttled("backup", now=BASE + 300) is False


def test_not_throttled_exactly_at_boundary(throttle):
    throttle.record_run("backup", now=BASE)
    # elapsed == min_interval_seconds → no longer throttled
    assert throttle.is_throttled("backup", now=BASE + 300) is False


def test_still_throttled_one_second_before_boundary(throttle):
    throttle.record_run("backup", now=BASE)
    assert throttle.is_throttled("backup", now=BASE + 299) is True


def test_seconds_until_allowed_before_run(throttle):
    assert throttle.seconds_until_allowed("backup", now=BASE) == 0


def test_seconds_until_allowed_right_after_run(throttle):
    throttle.record_run("backup", now=BASE)
    remaining = throttle.seconds_until_allowed("backup", now=BASE + 100)
    assert remaining == 200


def test_seconds_until_allowed_after_expiry(throttle):
    throttle.record_run("backup", now=BASE)
    assert throttle.seconds_until_allowed("backup", now=BASE + 400) == 0


def test_seconds_until_allowed_unregistered_job(throttle):
    assert throttle.seconds_until_allowed("ghost", now=BASE) == 0


def test_record_run_without_prior_register():
    t = JobThrottle()
    # Should not raise even if job was never registered
    t.record_run("adhoc", now=BASE)
    assert t.is_throttled("adhoc", now=BASE + 1) is False


def test_parse_throttle_rules_from_dicts():
    jobs = [
        {"name": "sync", "min_interval_seconds": 60},
        {"name": "report", "min_interval_seconds": 0},
        {"name": "ping"},
    ]
    rules = parse_throttle_rules(jobs)
    assert "sync" in rules
    assert rules["sync"].min_interval_seconds == 60
    assert "report" not in rules  # zero interval ignored
    assert "ping" not in rules    # no interval key


def test_parse_throttle_rules_string_integers():
    jobs = [{"name": "clean", "min_interval_seconds": "120"}]
    rules = parse_throttle_rules(jobs)
    assert rules["clean"].min_interval_seconds == 120
