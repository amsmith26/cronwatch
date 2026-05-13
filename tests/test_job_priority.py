"""Tests for cronwatch.job_priority."""
from __future__ import annotations

import pytest

from cronwatch.job_priority import (
    Priority,
    get_priority,
    jobs_at_or_above,
    parse_priority,
    sort_by_priority,
)


class _FakeJob:
    def __init__(self, name: str, priority=None):
        self.name = name
        self.extra = {"priority": priority} if priority is not None else {}


# ---------------------------------------------------------------------------
# parse_priority
# ---------------------------------------------------------------------------

def test_parse_priority_none_returns_normal():
    assert parse_priority(None) is Priority.NORMAL


def test_parse_priority_string_low():
    assert parse_priority("low") is Priority.LOW


def test_parse_priority_string_critical():
    assert parse_priority("critical") is Priority.CRITICAL


def test_parse_priority_string_case_insensitive():
    assert parse_priority("HIGH") is Priority.HIGH


def test_parse_priority_integer():
    assert parse_priority(3) is Priority.CRITICAL


def test_parse_priority_unknown_string_returns_normal():
    assert parse_priority("urgent") is Priority.NORMAL


def test_parse_priority_out_of_range_int_returns_normal():
    assert parse_priority(99) is Priority.NORMAL


# ---------------------------------------------------------------------------
# get_priority
# ---------------------------------------------------------------------------

def test_get_priority_reads_extra():
    job = _FakeJob("backup", priority="high")
    assert get_priority(job) is Priority.HIGH


def test_get_priority_no_extra_returns_normal():
    job = _FakeJob("backup")
    assert get_priority(job) is Priority.NORMAL


def test_get_priority_extra_none_returns_normal():
    job = _FakeJob("backup")
    job.extra = None  # type: ignore[assignment]
    assert get_priority(job) is Priority.NORMAL


# ---------------------------------------------------------------------------
# sort_by_priority
# ---------------------------------------------------------------------------

@pytest.fixture()
def jobs():
    return [
        _FakeJob("low_job", "low"),
        _FakeJob("critical_job", "critical"),
        _FakeJob("normal_job"),
        _FakeJob("high_job", "high"),
    ]


def test_sort_descending(jobs):
    result = sort_by_priority(jobs)
    priorities = [get_priority(j) for j in result]
    assert priorities == sorted(priorities, reverse=True)


def test_sort_ascending(jobs):
    result = sort_by_priority(jobs, descending=False)
    priorities = [get_priority(j) for j in result]
    assert priorities == sorted(priorities)


# ---------------------------------------------------------------------------
# jobs_at_or_above
# ---------------------------------------------------------------------------

def test_jobs_at_or_above_high(jobs):
    result = jobs_at_or_above(jobs, Priority.HIGH)
    names = {j.name for j in result}
    assert names == {"critical_job", "high_job"}


def test_jobs_at_or_above_low_returns_all(jobs):
    result = jobs_at_or_above(jobs, Priority.LOW)
    assert len(result) == len(jobs)


def test_jobs_at_or_above_critical_returns_one(jobs):
    result = jobs_at_or_above(jobs, Priority.CRITICAL)
    assert len(result) == 1
    assert result[0].name == "critical_job"
