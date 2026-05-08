"""Tests for cronwatch.notifier."""

import pytest
from cronwatch.notifier import Notifier


@pytest.fixture()
def notifier() -> Notifier:
    return Notifier(cooldown_seconds=300, max_suppressed=3)


JOB = "backup-db"


def test_should_notify_first_time(notifier: Notifier) -> None:
    """Always notify when no prior notification exists."""
    assert notifier.should_notify(JOB, _now=1000.0) is True


def test_should_not_notify_within_cooldown(notifier: Notifier) -> None:
    notifier.record_notified(JOB, _now=1000.0)
    assert notifier.should_notify(JOB, _now=1100.0) is False


def test_should_notify_after_cooldown_expires(notifier: Notifier) -> None:
    notifier.record_notified(JOB, _now=1000.0)
    assert notifier.should_notify(JOB, _now=1000.0 + 300) is True


def test_force_notify_after_max_suppressed(notifier: Notifier) -> None:
    notifier.record_notified(JOB, _now=1000.0)
    for _ in range(3):  # max_suppressed=3
        notifier.record_suppressed(JOB)
    assert notifier.should_notify(JOB, _now=1050.0) is True


def test_suppressed_count_resets_on_notify(notifier: Notifier) -> None:
    notifier.record_notified(JOB, _now=1000.0)
    notifier.record_suppressed(JOB)
    notifier.record_suppressed(JOB)
    notifier.record_notified(JOB, _now=1001.0)
    # suppressed_count should be 0 again; within cooldown → no notify
    assert notifier.should_notify(JOB, _now=1002.0) is False


def test_record_failure_increments(notifier: Notifier) -> None:
    assert notifier.record_failure(JOB) == 1
    assert notifier.record_failure(JOB) == 2
    assert notifier.consecutive_failures(JOB) == 2


def test_record_success_resets_failures(notifier: Notifier) -> None:
    notifier.record_failure(JOB)
    notifier.record_failure(JOB)
    notifier.record_success(JOB)
    assert notifier.consecutive_failures(JOB) == 0


def test_reset_clears_state(notifier: Notifier) -> None:
    notifier.record_notified(JOB, _now=9999.0)
    notifier.record_failure(JOB)
    notifier.reset(JOB)
    # After reset behaves like a brand-new job
    assert notifier.should_notify(JOB, _now=10000.0) is True
    assert notifier.consecutive_failures(JOB) == 0


def test_independent_state_per_job(notifier: Notifier) -> None:
    other = "cleanup-logs"
    notifier.record_notified(JOB, _now=1000.0)
    # other job has no state yet → should notify
    assert notifier.should_notify(other, _now=1050.0) is True
