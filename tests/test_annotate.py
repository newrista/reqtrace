"""Tests for reqtrace.annotate."""

import pytest
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.annotate import (
    annotate,
    get_annotation,
    get_all_annotations,
    remove_annotation,
    filter_by_annotation,
    clear_annotations,
)


def _make_entry(entry_id="e1", metadata=None):
    req = HttpRequest(
        method="GET",
        url="http://example.com/api/test",
        headers={},
        body=None,
    )
    resp = HttpResponse(status_code=200, headers={}, body=None)
    return TraceEntry(id=entry_id, request=req, response=resp, metadata=metadata)


def test_annotate_adds_key_value():
    entry = _make_entry()
    annotate(entry, "env", "production")
    assert entry.metadata["annotations"]["env"] == "production"


def test_annotate_updates_existing_key():
    entry = _make_entry()
    annotate(entry, "env", "staging")
    annotate(entry, "env", "production")
    assert entry.metadata["annotations"]["env"] == "production"


def test_annotate_works_with_none_metadata():
    entry = _make_entry(metadata=None)
    annotate(entry, "team", "backend")
    assert get_annotation(entry, "team") == "backend"


def test_annotate_works_with_existing_metadata():
    entry = _make_entry(metadata={"source": "proxy"})
    annotate(entry, "priority", 1)
    assert entry.metadata["source"] == "proxy"
    assert entry.metadata["annotations"]["priority"] == 1


def test_get_annotation_returns_default_when_missing():
    entry = _make_entry()
    assert get_annotation(entry, "nonexistent") is None
    assert get_annotation(entry, "nonexistent", default="fallback") == "fallback"


def test_get_all_annotations_empty():
    entry = _make_entry()
    assert get_all_annotations(entry) == {}


def test_get_all_annotations_returns_copy():
    entry = _make_entry()
    annotate(entry, "x", 1)
    result = get_all_annotations(entry)
    result["x"] = 999
    assert entry.metadata["annotations"]["x"] == 1


def test_remove_annotation_removes_key():
    entry = _make_entry()
    annotate(entry, "env", "prod")
    remove_annotation(entry, "env")
    assert get_annotation(entry, "env") is None


def test_remove_annotation_missing_key_is_noop():
    entry = _make_entry()
    remove_annotation(entry, "ghost")  # should not raise


def test_filter_by_annotation_key_only():
    e1 = _make_entry("e1")
    e2 = _make_entry("e2")
    e3 = _make_entry("e3")
    annotate(e1, "env", "prod")
    annotate(e2, "env", "staging")
    result = filter_by_annotation([e1, e2, e3], "env")
    assert e1 in result
    assert e2 in result
    assert e3 not in result


def test_filter_by_annotation_key_and_value():
    e1 = _make_entry("e1")
    e2 = _make_entry("e2")
    annotate(e1, "env", "prod")
    annotate(e2, "env", "staging")
    result = filter_by_annotation([e1, e2], "env", value="prod")
    assert result == [e1]


def test_clear_annotations_removes_all():
    entry = _make_entry()
    annotate(entry, "a", 1)
    annotate(entry, "b", 2)
    clear_annotations(entry)
    assert get_all_annotations(entry) == {}


def test_clear_annotations_no_metadata_is_noop():
    entry = _make_entry(metadata=None)
    clear_annotations(entry)  # should not raise
