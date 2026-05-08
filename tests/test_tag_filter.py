"""Tests for cronwatch.tag_filter."""
from __future__ import annotations

import pytest

from cronwatch.config import JobConfig
from cronwatch.tag_filter import (
    collect_all_tags,
    jobs_matching_tags,
    jobs_with_tag,
)


def _job(name: str, tags: list[str]) -> JobConfig:
    return JobConfig(name=name, schedule="* * * * *", command="true", tags=tags)


@pytest.fixture()
def jobs() -> list[JobConfig]:
    return [
        _job("backup", ["db", "nightly"]),
        _job("report", ["reporting", "nightly"]),
        _job("cleanup", ["db"]),
        _job("ping", []),
    ]


def test_jobs_with_tag_returns_matching(jobs):
    result = jobs_with_tag(jobs, "db")
    assert {j.name for j in result} == {"backup", "cleanup"}


def test_jobs_with_tag_case_insensitive(jobs):
    result = jobs_with_tag(jobs, "DB")
    assert len(result) == 2


def test_jobs_with_tag_no_match(jobs):
    result = jobs_with_tag(jobs, "nonexistent")
    assert result == []


def test_jobs_with_tag_empty_tags_job(jobs):
    result = jobs_with_tag(jobs, "nightly")
    assert "ping" not in {j.name for j in result}


def test_jobs_matching_tags_or_mode(jobs):
    result = jobs_matching_tags(jobs, ["db", "reporting"])
    names = {j.name for j in result}
    assert names == {"backup", "cleanup", "report"}


def test_jobs_matching_tags_and_mode(jobs):
    result = jobs_matching_tags(jobs, ["db", "nightly"], require_all=True)
    assert {j.name for j in result} == {"backup"}


def test_jobs_matching_tags_empty_tags_returns_all(jobs):
    result = jobs_matching_tags(jobs, [])
    assert len(result) == len(jobs)


def test_collect_all_tags_sorted_and_unique(jobs):
    tags = collect_all_tags(jobs)
    assert tags == ["db", "nightly", "reporting"]


def test_collect_all_tags_empty():
    assert collect_all_tags([]) == []


def test_collect_all_tags_no_tags_on_jobs():
    jobs_no_tags = [_job("a", []), _job("b", [])]
    assert collect_all_tags(jobs_no_tags) == []
