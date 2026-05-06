"""Tests for cronwatch.scheduler."""

import pytest

from cronwatch.scheduler import is_overdue, next_run, prev_run, seconds_until_next

# Fixed reference timestamp: 2024-01-15 10:00:00 UTC (Monday)
REF = 1705312800.0


def test_next_run_returns_future_timestamp() -> None:
    nxt = next_run("0 * * * *", base=REF)  # every hour
    assert nxt > REF


def test_next_run_hourly_is_one_hour_ahead() -> None:
    nxt = next_run("0 * * * *", base=REF)
    assert nxt == pytest.approx(REF + 3600, abs=5)


def test_prev_run_returns_past_timestamp() -> None:
    prv = prev_run("0 * * * *", base=REF)
    assert prv < REF


def test_prev_run_hourly_is_one_hour_behind() -> None:
    prv = prev_run("0 * * * *", base=REF)
    assert prv == pytest.approx(REF - 3600, abs=5)


def test_is_overdue_when_grace_exceeded() -> None:
    # Last run was exactly 1 hour ago; grace = 60s → overdue
    now = REF
    assert is_overdue("0 * * * *", grace_seconds=60, now=now) is True


def test_is_not_overdue_within_grace() -> None:
    # Simulate being only 30 seconds past the expected run with 120s grace
    prv = prev_run("0 * * * *", base=REF)
    now = prv + 30  # 30 seconds after last expected run
    assert is_overdue("0 * * * *", grace_seconds=120, now=now) is False


def test_seconds_until_next_positive() -> None:
    secs = seconds_until_next("0 * * * *", now=REF)
    assert secs > 0
    assert secs <= 3600


def test_seconds_until_next_consistency() -> None:
    nxt = next_run("*/15 * * * *", base=REF)
    secs = seconds_until_next("*/15 * * * *", now=REF)
    assert nxt - REF == pytest.approx(secs, abs=1)
