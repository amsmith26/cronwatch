"""Tests for cronwatch.job_annotations."""

import pytest

from cronwatch.job_annotations import Annotation, AnnotationSet, AnnotationStore


# ---------------------------------------------------------------------------
# Annotation
# ---------------------------------------------------------------------------

def test_annotation_str():
    ann = Annotation(key="env", value="prod")
    assert str(ann) == "env=prod"


# ---------------------------------------------------------------------------
# AnnotationSet
# ---------------------------------------------------------------------------

@pytest.fixture
def ann_set():
    return AnnotationSet(job_name="backup", run_id="run-001")


def test_add_and_get(ann_set):
    ann_set.add("env", "staging")
    assert ann_set.get("env") == "staging"


def test_get_missing_returns_default(ann_set):
    assert ann_set.get("missing") is None
    assert ann_set.get("missing", "fallback") == "fallback"


def test_add_overwrites_existing(ann_set):
    ann_set.add("env", "staging")
    ann_set.add("env", "prod")
    assert ann_set.get("env") == "prod"


def test_add_empty_key_raises(ann_set):
    with pytest.raises(ValueError):
        ann_set.add("", "value")


def test_remove_existing_returns_true(ann_set):
    ann_set.add("k", "v")
    assert ann_set.remove("k") is True
    assert ann_set.get("k") is None


def test_remove_missing_returns_false(ann_set):
    assert ann_set.remove("nope") is False


def test_as_list_sorted(ann_set):
    ann_set.add("z", "last")
    ann_set.add("a", "first")
    result = ann_set.as_list()
    assert [a.key for a in result] == ["a", "z"]


def test_len(ann_set):
    assert len(ann_set) == 0
    ann_set.add("x", "1")
    assert len(ann_set) == 1


# ---------------------------------------------------------------------------
# AnnotationStore
# ---------------------------------------------------------------------------

@pytest.fixture
def store():
    return AnnotationStore()


def test_annotate_creates_set(store):
    store.annotate("job1", "run-1", "env", "prod")
    ann = store.get_annotations("job1", "run-1")
    assert ann is not None
    assert ann.get("env") == "prod"


def test_get_annotations_missing_returns_none(store):
    assert store.get_annotations("ghost", "run-0") is None


def test_remove_annotation_present(store):
    store.annotate("job1", "run-1", "k", "v")
    assert store.remove_annotation("job1", "run-1", "k") is True


def test_remove_annotation_missing_job(store):
    assert store.remove_annotation("ghost", "run-0", "k") is False


def test_all_for_job_returns_sorted(store):
    store.annotate("job1", "run-2", "a", "1")
    store.annotate("job1", "run-1", "b", "2")
    store.annotate("job2", "run-x", "c", "3")
    result = store.all_for_job("job1")
    assert len(result) == 2
    assert result[0].run_id == "run-1"
    assert result[1].run_id == "run-2"


def test_clear_removes_set(store):
    store.annotate("job1", "run-1", "k", "v")
    store.clear("job1", "run-1")
    assert store.get_annotations("job1", "run-1") is None


def test_clear_nonexistent_is_noop(store):
    store.clear("ghost", "run-0")  # should not raise
