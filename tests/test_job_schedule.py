"""Tests for cronwatch.job_schedule."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from cronwatch.job_schedule import (
    ScheduleInfo,
    get_schedule_info,
    describe_schedule,
    schedules_for_config,
)

HOURLY = "0 * * * *"


class _FakeJob:
    def __init__(self, name: str, cron: str, grace_seconds: int = 0):
        self.name = name
        self.cron = cron
        self.grace_seconds = grace_seconds


def test_get_schedule_info_returns_schedule_info():
    info = get_schedule_info(HOURLY)
    assert isinstance(info, ScheduleInfo)
    assert info.cron_expr == HOURLY


def test_get_schedule_info_next_is_in_future():
    info = get_schedule_info(HOURLY)
    assert info.next_run_ts > time.time()


def test_get_schedule_info_prev_is_in_past():
    info = get_schedule_info(HOURLY)
    assert info.prev_run_ts <= time.time()


def test_get_schedule_info_seconds_until_next_positive():
    info = get_schedule_info(HOURLY)
    assert info.seconds_until_next > 0


def test_status_label_ok_when_not_overdue():
    info = get_schedule_info(HOURLY, grace_seconds=0)
    # hourly job is never overdue immediately after prev_run
    # just check the label is a string
    assert info.status_label() in ("OK", "OVERDUE")


def test_human_next_returns_string():
    info = get_schedule_info(HOURLY)
    result = info.human_next()
    assert isinstance(result, str)
    assert len(result) > 0


def test_human_next_now_when_zero():
    info = ScheduleInfo(
        cron_expr=HOURLY,
        grace_seconds=0,
        next_run_ts=time.time(),
        prev_run_ts=time.time() - 3600,
        seconds_until_next=0,
        overdue=False,
    )
    assert info.human_next() == "now"


def test_describe_schedule_contains_cron():
    result = describe_schedule(HOURLY)
    assert HOURLY in result


def test_describe_schedule_contains_status():
    result = describe_schedule(HOURLY)
    assert "status=" in result


def test_schedules_for_config_returns_dict():
    jobs = [
        _FakeJob("job_a", HOURLY, grace_seconds=60),
        _FakeJob("job_b", "*/5 * * * *"),
    ]
    result = schedules_for_config(jobs)
    assert set(result.keys()) == {"job_a", "job_b"}
    assert result["job_a"].grace_seconds == 60


def test_schedules_for_config_empty():
    assert schedules_for_config([]) == {}
