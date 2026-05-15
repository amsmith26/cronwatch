"""Tests for cronwatch.cost_config."""
import pytest
from cronwatch.cost_config import (
    build_cost_registry,
    cost_summary_lines,
    parse_cost_rule,
)
from cronwatch.job_cost import CostRegistry, CostRule


class _FakeJob:
    def __init__(self, name, cost=None):
        self.name = name
        self.cost = cost


def test_parse_cost_rule_none_returns_defaults():
    rule = parse_cost_rule("myjob", None)
    assert rule.job_name == "myjob"
    assert rule.cost_per_second == 0.0
    assert rule.fixed_cost == 0.0
    assert rule.currency == "USD"


def test_parse_cost_rule_empty_dict_returns_defaults():
    rule = parse_cost_rule("myjob", {})
    assert rule.cost_per_second == 0.0


def test_parse_cost_rule_partial_override():
    rule = parse_cost_rule("myjob", {"per_second": 0.02})
    assert rule.cost_per_second == pytest.approx(0.02)
    assert rule.fixed_cost == 0.0


def test_parse_cost_rule_full():
    rule = parse_cost_rule("myjob", {"per_second": 0.05, "fixed": 1.5, "currency": "GBP"})
    assert rule.cost_per_second == pytest.approx(0.05)
    assert rule.fixed_cost == pytest.approx(1.5)
    assert rule.currency == "GBP"


def test_parse_cost_rule_string_numbers_coerced():
    rule = parse_cost_rule("j", {"per_second": "0.1", "fixed": "2"})
    assert rule.cost_per_second == pytest.approx(0.1)
    assert rule.fixed_cost == pytest.approx(2.0)


def test_build_cost_registry_skips_jobs_without_cost():
    jobs = [_FakeJob("a"), _FakeJob("b")]
    reg = build_cost_registry(jobs)
    assert reg.total_cost("a") == 0.0
    assert reg.record("a", 10.0) is None


def test_build_cost_registry_registers_jobs_with_cost():
    jobs = [_FakeJob("a", cost={"per_second": 0.01})]
    reg = build_cost_registry(jobs)
    entry = reg.record("a", 10.0)
    assert entry is not None
    assert entry.total == pytest.approx(0.10)


def test_cost_summary_lines_no_data():
    reg = CostRegistry()
    lines = cost_summary_lines(reg)
    assert lines == ["No cost data available."]


def test_cost_summary_lines_with_data():
    reg = CostRegistry()
    reg.register(CostRule("backup", cost_per_second=0.01, fixed_cost=0.0))
    reg.record("backup", 100.0)
    lines = cost_summary_lines(reg)
    assert len(lines) == 1
    assert "backup" in lines[0]
    assert "1 run" in lines[0]
