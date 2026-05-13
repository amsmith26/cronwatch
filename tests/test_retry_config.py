"""Tests for cronwatch.retry_config."""
import pytest
from cronwatch.retry_config import parse_retry_policy
from cronwatch.job_retry import RetryPolicy


def test_none_returns_defaults():
    policy = parse_retry_policy(None)
    assert policy.max_attempts == 3
    assert policy.delay_seconds == 60.0
    assert policy.backoff_factor == 1.0
    assert policy.max_delay_seconds == 3600.0


def test_empty_dict_returns_defaults():
    policy = parse_retry_policy({})
    assert isinstance(policy, RetryPolicy)
    assert policy.max_attempts == 3


def test_partial_override():
    policy = parse_retry_policy({"max_attempts": 5})
    assert policy.max_attempts == 5
    assert policy.delay_seconds == 60.0  # unchanged


def test_full_override():
    raw = {
        "max_attempts": 10,
        "delay_seconds": 30.0,
        "backoff_factor": 2.0,
        "max_delay_seconds": 600.0,
    }
    policy = parse_retry_policy(raw)
    assert policy.max_attempts == 10
    assert policy.delay_seconds == 30.0
    assert policy.backoff_factor == 2.0
    assert policy.max_delay_seconds == 600.0


def test_string_integers_are_coerced():
    policy = parse_retry_policy({"max_attempts": "7", "delay_seconds": "45"})
    assert policy.max_attempts == 7
    assert policy.delay_seconds == 45.0


def test_invalid_values_fall_back_to_defaults():
    policy = parse_retry_policy({"max_attempts": "oops", "delay_seconds": None})
    assert policy.max_attempts == 3
    assert policy.delay_seconds == 60.0
