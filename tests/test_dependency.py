"""Tests for cronwatch.dependency and cronwatch.dependency_config."""

import time
import pytest

from cronwatch.dependency import (
    DependencyGraph,
    build_graph_from_config,
    dependencies_satisfied,
    blocked_jobs,
)
from cronwatch.dependency_config import (
    parse_depends_on,
    extract_dependency_map,
    detect_cycles,
)
from cronwatch.tracker import JobTracker, RunStatus, RunRecord
from cronwatch.config import JobConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _job(name, depends_on=None):
    return JobConfig(
        name=name,
        schedule="* * * * *",
        command=f"echo {name}",
        depends_on=depends_on or [],
    )


def _success_record(job_name, finished_at=None):
    now = finished_at or time.time()
    return RunRecord(
        job_name=job_name,
        started_at=now - 1,
        finished_at=now,
        status=RunStatus.SUCCESS,
        exit_code=0,
    )


def _failure_record(job_name):
    now = time.time()
    return RunRecord(
        job_name=job_name,
        started_at=now - 1,
        finished_at=now,
        status=RunStatus.FAILURE,
        exit_code=1,
    )


# ---------------------------------------------------------------------------
# DependencyGraph
# ---------------------------------------------------------------------------

def test_build_graph_from_config():
    jobs = [_job("a"), _job("b", depends_on=["a"]), _job("c", depends_on=["a", "b"])]
    graph = build_graph_from_config(jobs)
    assert graph.dependencies_of("b") == ["a"]
    assert graph.dependencies_of("c") == ["a", "b"]
    assert graph.dependencies_of("a") == []


def test_all_jobs_includes_deps_without_own_entry():
    graph = DependencyGraph()
    graph.add("b", ["a"])
    assert "a" in graph.all_jobs()
    assert "b" in graph.all_jobs()


# ---------------------------------------------------------------------------
# dependencies_satisfied
# ---------------------------------------------------------------------------

def test_satisfied_when_no_deps():
    graph = DependencyGraph()
    tracker = JobTracker()
    assert dependencies_satisfied("a", graph, tracker) is True


def test_not_satisfied_when_dep_has_no_records():
    graph = DependencyGraph()
    graph.add("b", ["a"])
    tracker = JobTracker()
    assert dependencies_satisfied("b", graph, tracker) is False


def test_not_satisfied_when_dep_failed():
    graph = DependencyGraph()
    graph.add("b", ["a"])
    tracker = JobTracker()
    tracker.records["a"] = [_failure_record("a")]
    assert dependencies_satisfied("b", graph, tracker) is False


def test_satisfied_when_dep_succeeded():
    graph = DependencyGraph()
    graph.add("b", ["a"])
    tracker = JobTracker()
    tracker.records["a"] = [_success_record("a")]
    assert dependencies_satisfied("b", graph, tracker) is True


def test_not_satisfied_when_dep_succeeded_before_since():
    graph = DependencyGraph()
    graph.add("b", ["a"])
    tracker = JobTracker()
    old_finish = time.time() - 3600
    tracker.records["a"] = [_success_record("a", finished_at=old_finish)]
    assert dependencies_satisfied("b", graph, tracker, since=time.time()) is False


# ---------------------------------------------------------------------------
# blocked_jobs
# ---------------------------------------------------------------------------

def test_blocked_jobs_returns_unsatisfied():
    graph = DependencyGraph()
    graph.add("b", ["a"])
    graph.add("c", ["b"])
    tracker = JobTracker()
    tracker.records["b"] = [_success_record("b")]
    # "a" has no records -> "b" blocked; "b" ok -> "c" not blocked
    blocked = blocked_jobs(graph, tracker)
    assert "b" in blocked
    assert "c" not in blocked


# ---------------------------------------------------------------------------
# dependency_config helpers
# ---------------------------------------------------------------------------

def test_parse_depends_on_none():
    assert parse_depends_on(None) == []


def test_parse_depends_on_string():
    assert parse_depends_on("fetch") == ["fetch"]


def test_parse_depends_on_list():
    assert parse_depends_on(["a", "b"]) == ["a", "b"]


def test_parse_depends_on_invalid_raises():
    with pytest.raises(ValueError):
        parse_depends_on(42)


def test_extract_dependency_map():
    raw = [
        {"name": "a", "schedule": "* * * * *", "command": "echo a"},
        {"name": "b", "schedule": "* * * * *", "command": "echo b", "depends_on": "a"},
    ]
    result = extract_dependency_map(raw)
    assert result == {"b": ["a"]}


def test_detect_cycles_none():
    dep_map = {"b": ["a"], "c": ["b"]}
    assert detect_cycles(dep_map) == []


def test_detect_cycles_simple_cycle():
    dep_map = {"a": ["b"], "b": ["a"]}
    cycle = detect_cycles(dep_map)
    assert len(cycle) > 0
