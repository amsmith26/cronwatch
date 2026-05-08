"""Tests for cronwatch.rate_limiter."""

import time
import pytest

from cronwatch.rate_limiter import RateLimiter


@pytest.fixture()
def limiter() -> RateLimiter:
    """A limiter that allows 3 alerts per hour."""
    return RateLimiter(max_alerts=3, window_secs=3600.0)


# ---------------------------------------------------------------------------
# Basic allow / deny behaviour
# ---------------------------------------------------------------------------

def test_first_alert_is_allowed(limiter: RateLimiter) -> None:
    assert limiter.is_allowed("backup") is True


def test_burst_up_to_capacity_is_allowed(limiter: RateLimiter) -> None:
    job = "deploy"
    results = [limiter.is_allowed(job) for _ in range(3)]
    assert all(results), "All burst tokens should be consumed successfully"


def test_exceeding_capacity_is_denied(limiter: RateLimiter) -> None:
    job = "sync"
    for _ in range(3):
        limiter.is_allowed(job)          # drain the bucket
    assert limiter.is_allowed(job) is False


def test_different_jobs_have_independent_buckets(limiter: RateLimiter) -> None:
    for _ in range(3):
        limiter.is_allowed("job_a")
    # job_b bucket should still be full
    assert limiter.is_allowed("job_b") is True


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def test_reset_refills_bucket(limiter: RateLimiter) -> None:
    job = "cleanup"
    for _ in range(3):
        limiter.is_allowed(job)
    assert limiter.is_allowed(job) is False
    limiter.reset(job)
    assert limiter.is_allowed(job) is True


def test_reset_unknown_job_is_safe(limiter: RateLimiter) -> None:
    limiter.reset("nonexistent")   # should not raise


# ---------------------------------------------------------------------------
# Remaining tokens
# ---------------------------------------------------------------------------

def test_remaining_starts_at_capacity(limiter: RateLimiter) -> None:
    assert limiter.remaining("fresh") == pytest.approx(3.0)


def test_remaining_decreases_after_consume(limiter: RateLimiter) -> None:
    job = "monitor"
    limiter.is_allowed(job)
    assert limiter.remaining(job) == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# Token refill over time (fast, using a tiny window)
# ---------------------------------------------------------------------------

def test_tokens_refill_over_time() -> None:
    fast = RateLimiter(max_alerts=2, window_secs=0.2)  # 10 tokens/s
    job = "heartbeat"
    fast.is_allowed(job)
    fast.is_allowed(job)          # drain both tokens
    assert fast.is_allowed(job) is False
    time.sleep(0.15)              # wait for ~1.5 tokens to refill
    assert fast.is_allowed(job) is True


# ---------------------------------------------------------------------------
# Constructor validation
# ---------------------------------------------------------------------------

def test_invalid_max_alerts_raises() -> None:
    with pytest.raises(ValueError, match="max_alerts"):
        RateLimiter(max_alerts=0)


def test_invalid_window_raises() -> None:
    with pytest.raises(ValueError, match="window_secs"):
        RateLimiter(max_alerts=5, window_secs=0)
