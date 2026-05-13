"""Tests for cronwatch.job_concurrency."""
import pytest

from cronwatch.job_concurrency import (
    ConcurrencyRule,
    JobConcurrencyGuard,
    parse_concurrency_rule,
)


@pytest.fixture()
def guard() -> JobConcurrencyGuard:
    return JobConcurrencyGuard()


def test_unregistered_job_is_always_allowed(guard):
    assert guard.acquire("unregistered") is True


def test_unregistered_job_not_at_limit(guard):
    assert guard.is_at_limit("unregistered") is False


def test_first_acquire_is_granted(guard):
    guard.register("backup", ConcurrencyRule(max_concurrent=2))
    assert guard.acquire("backup") is True


def test_acquire_up_to_limit_is_granted(guard):
    guard.register("sync", ConcurrencyRule(max_concurrent=3))
    assert guard.acquire("sync") is True
    assert guard.acquire("sync") is True
    assert guard.acquire("sync") is True


def test_exceeding_limit_is_denied(guard):
    guard.register("report", ConcurrencyRule(max_concurrent=1))
    assert guard.acquire("report") is True
    assert guard.acquire("report") is False


def test_release_frees_slot(guard):
    guard.register("report", ConcurrencyRule(max_concurrent=1))
    guard.acquire("report")
    guard.release("report")
    assert guard.acquire("report") is True


def test_running_count_tracks_acquires(guard):
    guard.register("job", ConcurrencyRule(max_concurrent=5))
    guard.acquire("job")
    guard.acquire("job")
    assert guard.running_count("job") == 2


def test_running_count_decrements_on_release(guard):
    guard.register("job", ConcurrencyRule(max_concurrent=5))
    guard.acquire("job")
    guard.acquire("job")
    guard.release("job")
    assert guard.running_count("job") == 1


def test_release_below_zero_is_safe(guard):
    guard.register("job", ConcurrencyRule(max_concurrent=1))
    guard.release("job")  # never acquired
    assert guard.running_count("job") == 0


def test_is_at_limit_true_when_full(guard):
    guard.register("job", ConcurrencyRule(max_concurrent=1))
    guard.acquire("job")
    assert guard.is_at_limit("job") is True


def test_is_at_limit_false_when_slot_free(guard):
    guard.register("job", ConcurrencyRule(max_concurrent=2))
    guard.acquire("job")
    assert guard.is_at_limit("job") is False


def test_different_jobs_are_independent(guard):
    guard.register("a", ConcurrencyRule(max_concurrent=1))
    guard.register("b", ConcurrencyRule(max_concurrent=1))
    guard.acquire("a")
    assert guard.acquire("b") is True


# --- parse_concurrency_rule ---

def test_parse_none_returns_defaults():
    rule = parse_concurrency_rule(None)
    assert rule.max_concurrent == 1


def test_parse_empty_dict_returns_defaults():
    rule = parse_concurrency_rule({})
    assert rule.max_concurrent == 1


def test_parse_sets_max_concurrent():
    rule = parse_concurrency_rule({"max_concurrent": 4})
    assert rule.max_concurrent == 4


def test_parse_string_integer_is_coerced():
    rule = parse_concurrency_rule({"max_concurrent": "3"})
    assert rule.max_concurrent == 3


def test_parse_zero_clamped_to_one():
    rule = parse_concurrency_rule({"max_concurrent": 0})
    assert rule.max_concurrent == 1
