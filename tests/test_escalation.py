"""Tests for cronwatch.escalation."""

import pytest
from cronwatch.escalation import EscalationPolicy, EscalationTracker


@pytest.fixture()
def policy() -> EscalationPolicy:
    return EscalationPolicy(warn_after=2, critical_after=4, reset_after=2)


@pytest.fixture()
def tracker(policy: EscalationPolicy) -> EscalationTracker:
    return EscalationTracker(policy=policy)


# ---------------------------------------------------------------------------
# Failure escalation
# ---------------------------------------------------------------------------

def test_initial_level_is_ok(tracker: EscalationTracker) -> None:
    assert tracker.current_level("job") == "ok"


def test_first_failure_still_ok(tracker: EscalationTracker) -> None:
    level = tracker.record_failure("job")
    assert level == "ok"


def test_warn_threshold(tracker: EscalationTracker) -> None:
    tracker.record_failure("job")
    level = tracker.record_failure("job")
    assert level == "warn"


def test_critical_threshold(tracker: EscalationTracker) -> None:
    for _ in range(4):
        level = tracker.record_failure("job")
    assert level == "critical"


def test_consecutive_failures_counter(tracker: EscalationTracker) -> None:
    for i in range(3):
        tracker.record_failure("job")
    assert tracker.consecutive_failures("job") == 3


# ---------------------------------------------------------------------------
# Recovery / reset
# ---------------------------------------------------------------------------

def test_single_success_does_not_reset_when_reset_after_2(
    tracker: EscalationTracker,
) -> None:
    tracker.record_failure("job")
    tracker.record_failure("job")
    tracker.record_success("job")
    assert tracker.current_level("job") == "warn"


def test_two_successes_reset_to_ok(tracker: EscalationTracker) -> None:
    tracker.record_failure("job")
    tracker.record_failure("job")
    tracker.record_success("job")
    level = tracker.record_success("job")
    assert level == "ok"
    assert tracker.consecutive_failures("job") == 0


def test_hard_reset_clears_state(tracker: EscalationTracker) -> None:
    tracker.record_failure("job")
    tracker.record_failure("job")
    tracker.reset("job")
    assert tracker.current_level("job") == "ok"
    assert tracker.consecutive_failures("job") == 0


# ---------------------------------------------------------------------------
# Isolation between jobs
# ---------------------------------------------------------------------------

def test_different_jobs_are_independent(tracker: EscalationTracker) -> None:
    for _ in range(4):
        tracker.record_failure("job_a")
    assert tracker.current_level("job_a") == "critical"
    assert tracker.current_level("job_b") == "ok"
