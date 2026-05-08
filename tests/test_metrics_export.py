"""Tests for cronwatch.metrics_export."""
import pytest
from cronwatch.metrics import MetricsRegistry
from cronwatch.metrics_export import render_prometheus, render_text


@pytest.fixture()
def reg() -> MetricsRegistry:
    r = MetricsRegistry()
    r.record_success("backup", 10.0)
    r.record_success("backup", 20.0)
    r.record_failure("backup", 5.0)
    r.record_missed("cleanup")
    return r


def test_prometheus_contains_job_label(reg):
    out = render_prometheus(reg)
    assert 'job="backup"' in out
    assert 'job="cleanup"' in out


def test_prometheus_total_runs(reg):
    out = render_prometheus(reg)
    assert 'cronwatch_total_runs{job="backup"} 3' in out


def test_prometheus_missed_runs(reg):
    out = render_prometheus(reg)
    assert 'cronwatch_missed_runs{job="cleanup"} 1' in out


def test_prometheus_success_rate(reg):
    out = render_prometheus(reg)
    assert 'cronwatch_success_rate{job="backup"}' in out


def test_prometheus_avg_duration(reg):
    out = render_prometheus(reg)
    # avg of 10 + 20 over 2 successes = 15.0
    assert 'cronwatch_avg_duration_seconds{job="backup"} 15.0' in out


def test_prometheus_no_last_failure_when_all_success():
    r = MetricsRegistry()
    r.record_success("ok_job", 1.0)
    out = render_prometheus(r)
    assert 'last_failure_timestamp' not in out


def test_text_render_contains_header(reg):
    out = render_text(reg)
    assert "Job" in out
    assert "Runs" in out


def test_text_render_contains_job_name(reg):
    out = render_text(reg)
    assert "backup" in out
    assert "cleanup" in out


def test_text_render_empty_registry():
    r = MetricsRegistry()
    out = render_text(r)
    assert "No metrics" in out
