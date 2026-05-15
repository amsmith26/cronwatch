"""Tests for cronwatch.job_cost."""
import pytest
from cronwatch.job_cost import CostEntry, CostRegistry, CostRule


@pytest.fixture
def registry() -> CostRegistry:
    reg = CostRegistry()
    reg.register(CostRule(job_name="backup", cost_per_second=0.01, fixed_cost=0.05, currency="USD"))
    reg.register(CostRule(job_name="report", cost_per_second=0.0, fixed_cost=1.0, currency="EUR"))
    return reg


def test_record_returns_cost_entry(registry):
    entry = registry.record("backup", duration_seconds=10.0)
    assert isinstance(entry, CostEntry)
    assert entry.job_name == "backup"


def test_record_variable_cost(registry):
    entry = registry.record("backup", duration_seconds=10.0)
    assert entry.variable_cost == pytest.approx(0.10)


def test_record_fixed_cost(registry):
    entry = registry.record("backup", duration_seconds=10.0)
    assert entry.fixed_cost == pytest.approx(0.05)


def test_record_total_cost(registry):
    entry = registry.record("backup", duration_seconds=10.0)
    assert entry.total == pytest.approx(0.15)


def test_record_unregistered_job_returns_none(registry):
    result = registry.record("unknown", duration_seconds=5.0)
    assert result is None


def test_total_cost_accumulates(registry):
    registry.record("backup", duration_seconds=10.0)
    registry.record("backup", duration_seconds=20.0)
    # 0.15 + 0.25 = 0.40
    assert registry.total_cost("backup") == pytest.approx(0.40)


def test_total_cost_unknown_job_is_zero(registry):
    assert registry.total_cost("ghost") == 0.0


def test_all_entries_returns_list(registry):
    registry.record("backup", 5.0)
    registry.record("backup", 5.0)
    assert len(registry.all_entries("backup")) == 2


def test_summary_keys(registry):
    registry.record("backup", 1.0)
    registry.record("report", 1.0)
    s = registry.summary()
    assert "backup" in s
    assert "report" in s


def test_fixed_only_job(registry):
    entry = registry.record("report", duration_seconds=100.0)
    assert entry.variable_cost == pytest.approx(0.0)
    assert entry.total == pytest.approx(1.0)
    assert entry.currency == "EUR"
