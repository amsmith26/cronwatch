"""Tests for cronwatch.escalation_config."""

import pytest
from cronwatch.escalation import EscalationPolicy
from cronwatch.escalation_config import parse_escalation_policy


def test_none_returns_defaults() -> None:
    p = parse_escalation_policy(None)
    assert p == EscalationPolicy()


def test_empty_dict_returns_defaults() -> None:
    p = parse_escalation_policy({})
    assert p == EscalationPolicy()


def test_partial_override() -> None:
    p = parse_escalation_policy({"warn_after": 3})
    assert p.warn_after == 3
    assert p.critical_after == EscalationPolicy().critical_after


def test_full_override() -> None:
    p = parse_escalation_policy(
        {"warn_after": 1, "critical_after": 3, "reset_after": 2}
    )
    assert p.warn_after == 1
    assert p.critical_after == 3
    assert p.reset_after == 2


def test_string_integers_are_coerced() -> None:
    p = parse_escalation_policy({"warn_after": "2", "critical_after": "6"})
    assert p.warn_after == 2
    assert p.critical_after == 6


def test_invalid_type_raises() -> None:
    with pytest.raises(ValueError, match="warn_after"):
        parse_escalation_policy({"warn_after": "abc"})


def test_warn_after_zero_raises() -> None:
    with pytest.raises(ValueError, match="warn_after"):
        parse_escalation_policy({"warn_after": 0})


def test_critical_less_than_warn_raises() -> None:
    with pytest.raises(ValueError, match="critical_after"):
        parse_escalation_policy({"warn_after": 5, "critical_after": 3})


def test_reset_after_zero_raises() -> None:
    with pytest.raises(ValueError, match="reset_after"):
        parse_escalation_policy({"reset_after": 0})
