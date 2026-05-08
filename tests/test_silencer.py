"""Tests for cronwatch.silencer."""

from datetime import datetime, timedelta, timezone

import pytest

from cronwatch.silencer import (
    Silencer,
    SilenceRule,
    parse_silence_rules,
    _parse_dt,
)


UTC = timezone.utc


def _now() -> datetime:
    return datetime.now(UTC)


@pytest.fixture
def rule() -> SilenceRule:
    now = _now()
    return SilenceRule(
        job_pattern="backup-*",
        start=now - timedelta(hours=1),
        end=now + timedelta(hours=1),
        reason="maintenance",
    )


@pytest.fixture
def silencer(rule) -> Silencer:
    s = Silencer()
    s.add_rule(rule)
    return s


# --- SilenceRule ---

def test_matches_job_exact():
    r = SilenceRule("backup-db", _now(), _now() + timedelta(hours=1))
    assert r.matches_job("backup-db")
    assert not r.matches_job("backup-files")


def test_matches_job_wildcard(rule):
    assert rule.matches_job("backup-db")
    assert rule.matches_job("backup-files")
    assert not rule.matches_job("cleanup")


def test_is_active_within_window(rule):
    assert rule.is_active()


def test_is_active_before_window():
    future = _now() + timedelta(hours=2)
    r = SilenceRule("job", future, future + timedelta(hours=1))
    assert not r.is_active()


def test_is_active_after_window():
    past_end = _now() - timedelta(hours=1)
    r = SilenceRule("job", past_end - timedelta(hours=1), past_end)
    assert not r.is_active()


def test_suppresses_matching_active_rule(rule):
    assert rule.suppresses("backup-db")


def test_suppresses_non_matching_job(rule):
    assert not rule.suppresses("cleanup")


# --- Silencer ---

def test_is_silenced_true(silencer):
    assert silencer.is_silenced("backup-db")


def test_is_silenced_false(silencer):
    assert not silencer.is_silenced("cleanup")


def test_active_rules_returns_active(silencer, rule):
    assert rule in silencer.active_rules()


def test_expire_rules_removes_past_rules():
    s = Silencer()
    past = _now() - timedelta(hours=2)
    s.add_rule(SilenceRule("job", past, past + timedelta(minutes=30)))
    removed = s.expire_rules()
    assert removed == 1
    assert len(s.rules) == 0


def test_expire_rules_keeps_active(silencer):
    removed = silencer.expire_rules()
    assert removed == 0
    assert len(silencer.rules) == 1


# --- parse_silence_rules ---

def test_parse_silence_rules_basic():
    raw = [
        {
            "job": "backup-*",
            "start": "2030-01-01T00:00:00",
            "end": "2030-01-01T06:00:00",
            "reason": "planned maintenance",
        }
    ]
    rules = parse_silence_rules(raw)
    assert len(rules) == 1
    assert rules[0].job_pattern == "backup-*"
    assert rules[0].reason == "planned maintenance"
    assert rules[0].start.tzinfo == UTC


def test_parse_silence_rules_empty():
    assert parse_silence_rules([]) == []
    assert parse_silence_rules(None) == []


def test_parse_dt_naive_gets_utc():
    dt = _parse_dt("2030-06-15T12:00:00")
    assert dt.tzinfo == UTC


def test_parse_dt_aware_preserved():
    dt = _parse_dt("2030-06-15T12:00:00+00:00")
    assert dt.tzinfo is not None
