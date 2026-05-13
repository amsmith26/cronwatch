"""Tests for cronwatch.job_labels."""

from __future__ import annotations

import pytest

from cronwatch.job_labels import (
    collect_label_keys,
    get_labels,
    has_label,
    jobs_with_label,
    label_index,
)


class _FakeJob:
    def __init__(self, name: str, labels: dict | None = None):
        self.name = name
        self.labels = labels


@pytest.fixture()
def jobs():
    return [
        _FakeJob("backup", {"env": "prod", "team": "ops"}),
        _FakeJob("report", {"env": "prod", "team": "data"}),
        _FakeJob("cleanup", {"env": "staging"}),
        _FakeJob("nolabels", None),
    ]


def test_get_labels_returns_dict(jobs):
    assert get_labels(jobs[0]) == {"env": "prod", "team": "ops"}


def test_get_labels_none_returns_empty(jobs):
    assert get_labels(jobs[3]) == {}


def test_has_label_key_only(jobs):
    assert has_label(jobs[0], "env") is True
    assert has_label(jobs[3], "env") is False


def test_has_label_key_and_value(jobs):
    assert has_label(jobs[0], "env", "prod") is True
    assert has_label(jobs[0], "env", "staging") is False


def test_jobs_with_label_key_only(jobs):
    result = jobs_with_label(jobs, "env")
    assert len(result) == 3
    assert jobs[3] not in result


def test_jobs_with_label_key_and_value(jobs):
    result = jobs_with_label(jobs, "env", "prod")
    assert len(result) == 2
    names = {j.name for j in result}
    assert names == {"backup", "report"}


def test_jobs_with_label_no_match(jobs):
    assert jobs_with_label(jobs, "nonexistent") == []


def test_collect_label_keys_sorted(jobs):
    keys = collect_label_keys(jobs)
    assert keys == ["env", "team"]


def test_collect_label_keys_empty():
    assert collect_label_keys([]) == []


def test_label_index_structure(jobs):
    idx = label_index(jobs)
    assert "prod" in idx["env"]
    assert len(idx["env"]["prod"]) == 2
    assert len(idx["env"]["staging"]) == 1
    assert "ops" in idx["team"]
    assert "data" in idx["team"]


def test_label_index_no_labels():
    assert label_index([_FakeJob("x", None)]) == {}
