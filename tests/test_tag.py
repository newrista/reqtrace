"""Tests for reqtrace/tag.py"""

import pytest
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.tag import (
    add_tag, remove_tag, filter_by_tag, filter_by_any_tag,
    filter_by_all_tags, list_tags, auto_tag,
)


def _make_entry(entry_id="1", method="GET", status=200, tags=None) -> TraceEntry:
    req = HttpRequest(method=method, url="http://example.com/api/test")
    resp = HttpResponse(status_code=status)
    return TraceEntry(id=entry_id, request=req, response=resp,
                      timestamp="2024-01-01T00:00:00Z", tags=list(tags or []))


def test_add_tag_adds_new_tag():
    entry = _make_entry()
    updated = add_tag(entry, "smoke")
    assert "smoke" in updated.tags


def test_add_tag_no_duplicates():
    entry = _make_entry(tags=["smoke"])
    updated = add_tag(entry, "smoke")
    assert updated.tags.count("smoke") == 1


def test_remove_tag_removes_existing():
    entry = _make_entry(tags=["smoke", "regression"])
    updated = remove_tag(entry, "smoke")
    assert "smoke" not in updated.tags
    assert "regression" in updated.tags


def test_remove_tag_missing_is_noop():
    entry = _make_entry(tags=["regression"])
    updated = remove_tag(entry, "nonexistent")
    assert updated.tags == ["regression"]


def test_filter_by_tag_returns_matching():
    entries = [
        _make_entry("1", tags=["smoke"]),
        _make_entry("2", tags=["regression"]),
        _make_entry("3", tags=["smoke", "regression"]),
    ]
    result = filter_by_tag(entries, "smoke")
    assert len(result) == 2
    assert all("smoke" in e.tags for e in result)


def test_filter_by_any_tag():
    entries = [
        _make_entry("1", tags=["a"]),
        _make_entry("2", tags=["b"]),
        _make_entry("3", tags=["c"]),
    ]
    result = filter_by_any_tag(entries, ["a", "b"])
    assert len(result) == 2


def test_filter_by_all_tags():
    entries = [
        _make_entry("1", tags=["a", "b"]),
        _make_entry("2", tags=["a"]),
        _make_entry("3", tags=["b"]),
    ]
    result = filter_by_all_tags(entries, ["a", "b"])
    assert len(result) == 1
    assert result[0].id == "1"


def test_list_tags_returns_sorted_unique():
    entries = [
        _make_entry("1", tags=["z", "a"]),
        _make_entry("2", tags=["a", "m"]),
    ]
    tags = list_tags(entries)
    assert tags == ["a", "m", "z"]


def test_auto_tag_adds_method_and_success():
    entry = _make_entry(method="GET", status=200)
    updated = auto_tag(entry)
    assert "GET" in updated.tags
    assert "success" in updated.tags


def test_auto_tag_client_error():
    entry = _make_entry(method="POST", status=404)
    updated = auto_tag(entry)
    assert "client-error" in updated.tags
    assert "success" not in updated.tags


def test_auto_tag_server_error():
    entry = _make_entry(method="GET", status=500)
    updated = auto_tag(entry)
    assert "server-error" in updated.tags
