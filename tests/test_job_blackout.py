"""Tests for cronwatch.job_blackout."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from cronwatch.job_blackout import (
    BlackoutWindow,
    JobBlackout,
    parse_blackout_windows,
)

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
_BEFORE = _NOW - timedelta(hours=1)
_AFTER = _NOW + timedelta(hours=1)


@pytest.fixture()
def window() -> BlackoutWindow:
    return BlackoutWindow(
        name="maintenance",
        start=_BEFORE,
        end=_AFTER,
        jobs=["backup-*", "sync"],
    )


@pytest.fixture()
def blackout(window: BlackoutWindow) -> JobBlackout:
    return JobBlackout([window])


# --- BlackoutWindow ---------------------------------------------------------

def test_is_active_within_window(window: BlackoutWindow) -> None:
    assert window.is_active(_NOW) is True


def test_is_active_before_window(window: BlackoutWindow) -> None:
    assert window.is_active(_BEFORE - timedelta(seconds=1)) is False


def test_is_active_at_end_is_exclusive(window: BlackoutWindow) -> None:
    assert window.is_active(_AFTER) is False


def test_matches_job_by_glob(window: BlackoutWindow) -> None:
    assert window.matches_job("backup-daily") is True


def test_matches_job_exact(window: BlackoutWindow) -> None:
    assert window.matches_job("sync") is True


def test_matches_job_no_match(window: BlackoutWindow) -> None:
    assert window.matches_job("report") is False


def test_matches_all_jobs_when_list_empty() -> None:
    w = BlackoutWindow(name="all", start=_BEFORE, end=_AFTER, jobs=[])
    assert w.matches_job("anything") is True


def test_suppresses_active_matching(window: BlackoutWindow) -> None:
    assert window.suppresses("backup-weekly", _NOW) is True


def test_suppresses_inactive_window(window: BlackoutWindow) -> None:
    assert window.suppresses("backup-weekly", _AFTER) is False


def test_suppresses_active_but_nonmatching(window: BlackoutWindow) -> None:
    assert window.suppresses("report", _NOW) is False


# --- JobBlackout ------------------------------------------------------------

def test_is_blacked_out_true(blackout: JobBlackout) -> None:
    assert blackout.is_blacked_out("backup-daily", _NOW) is True


def test_is_blacked_out_false_wrong_job(blackout: JobBlackout) -> None:
    assert blackout.is_blacked_out("report", _NOW) is False


def test_is_blacked_out_false_outside_window(blackout: JobBlackout) -> None:
    assert blackout.is_blacked_out("backup-daily", _AFTER) is False


def test_active_windows_for_returns_matching(blackout: JobBlackout, window: BlackoutWindow) -> None:
    result = blackout.active_windows_for("sync", _NOW)
    assert result == [window]


def test_active_windows_for_empty_when_inactive(blackout: JobBlackout) -> None:
    result = blackout.active_windows_for("sync", _AFTER)
    assert result == []


def test_add_window_extends_collection(blackout: JobBlackout) -> None:
    extra = BlackoutWindow(name="extra", start=_BEFORE, end=_AFTER, jobs=[])
    blackout.add(extra)
    assert len(blackout.all_windows()) == 2


# --- parse_blackout_windows -------------------------------------------------

def test_parse_empty_returns_empty() -> None:
    assert parse_blackout_windows(None) == []
    assert parse_blackout_windows([]) == []


def test_parse_dict_list() -> None:
    raw = [
        {
            "name": "deploy",
            "start": "2024-06-01T11:00:00+00:00",
            "end": "2024-06-01T13:00:00+00:00",
            "jobs": ["deploy-*"],
        }
    ]
    windows = parse_blackout_windows(raw)
    assert len(windows) == 1
    assert windows[0].name == "deploy"
    assert windows[0].matches_job("deploy-prod") is True
    assert windows[0].is_active(_NOW) is True


def test_parse_naive_datetime_assumes_utc() -> None:
    raw = [
        {
            "name": "naive",
            "start": "2024-06-01T11:00:00",
            "end": "2024-06-01T13:00:00",
        }
    ]
    windows = parse_blackout_windows(raw)
    assert windows[0].start.tzinfo == timezone.utc
