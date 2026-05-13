"""Tests for cronwatch.job_retry."""
import pytest
from cronwatch.job_retry import RetryPolicy, RetryState, run_with_retry


# ---------------------------------------------------------------------------
# RetryPolicy.delay_for
# ---------------------------------------------------------------------------

def test_delay_for_first_attempt_is_zero():
    policy = RetryPolicy(delay_seconds=30.0)
    assert policy.delay_for(0) == 0.0


def test_delay_for_second_attempt_equals_base():
    policy = RetryPolicy(delay_seconds=30.0, backoff_factor=1.0)
    assert policy.delay_for(1) == 30.0


def test_delay_for_exponential_backoff():
    policy = RetryPolicy(delay_seconds=10.0, backoff_factor=2.0)
    assert policy.delay_for(1) == 10.0
    assert policy.delay_for(2) == 20.0
    assert policy.delay_for(3) == 40.0


def test_delay_capped_at_max():
    policy = RetryPolicy(delay_seconds=100.0, backoff_factor=10.0, max_delay_seconds=150.0)
    assert policy.delay_for(2) == 150.0


# ---------------------------------------------------------------------------
# run_with_retry
# ---------------------------------------------------------------------------

def test_success_on_first_try():
    calls = []
    policy = RetryPolicy(max_attempts=3, delay_seconds=0)

    def fn():
        calls.append(1)
        return True

    state = run_with_retry(fn, policy, sleep=lambda _: None)
    assert state.succeeded is True
    assert state.attempts == 1
    assert len(calls) == 1


def test_success_on_third_try():
    results = [False, False, True]
    policy = RetryPolicy(max_attempts=3, delay_seconds=0)
    state = run_with_retry(lambda: results.pop(0), policy, sleep=lambda _: None)
    assert state.succeeded is True
    assert state.attempts == 3


def test_exhausted_after_all_failures():
    policy = RetryPolicy(max_attempts=4, delay_seconds=0)
    state = run_with_retry(lambda: False, policy, sleep=lambda _: None)
    assert state.succeeded is False
    assert state.exhausted is True
    assert state.attempts == 4


def test_sleep_called_between_attempts():
    sleeps: list = []
    policy = RetryPolicy(max_attempts=3, delay_seconds=10.0, backoff_factor=1.0)
    run_with_retry(lambda: False, policy, sleep=sleeps.append)
    # first attempt has no delay; subsequent two do
    assert sleeps == [10.0, 10.0]


def test_sleep_uses_backoff():
    sleeps: list = []
    policy = RetryPolicy(max_attempts=3, delay_seconds=5.0, backoff_factor=2.0)
    run_with_retry(lambda: False, policy, sleep=sleeps.append)
    assert sleeps == [5.0, 10.0]
