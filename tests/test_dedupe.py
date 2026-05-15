"""Tests for reqtrace.dedupe module."""

import pytest
from datetime import datetime
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.dedupe import dedupe, find_duplicates, count_unique, has_duplicates


def _make_entry(method="GET", path="/api/test", query=None, body=None, status=200, entry_id=None):
    req = HttpRequest(
        method=method,
        path=path,
        query_params=query or {},
        headers={"host": "example.com"},
        body=body,
    )
    resp = HttpResponse(
        status_code=status,
        headers={"content-type": "application/json"},
        body=b'{"ok": true}',
    )
    return TraceEntry(
        id=entry_id or f"{method}-{path}",
        request=req,
        response=resp,
        timestamp=datetime.utcnow(),
    )


def test_dedupe_removes_exact_duplicates():
    e1 = _make_entry("GET", "/api/foo", entry_id="a")
    e2 = _make_entry("GET", "/api/foo", entry_id="b")
    result = dedupe([e1, e2])
    assert len(result) == 1
    assert result[0].id == "a"


def test_dedupe_keeps_different_methods():
    e1 = _make_entry("GET", "/api/foo", entry_id="a")
    e2 = _make_entry("POST", "/api/foo", entry_id="b")
    result = dedupe([e1, e2])
    assert len(result) == 2


def test_dedupe_keeps_different_paths():
    e1 = _make_entry("GET", "/api/foo", entry_id="a")
    e2 = _make_entry("GET", "/api/bar", entry_id="b")
    result = dedupe([e1, e2])
    assert len(result) == 2


def test_dedupe_distinguishes_query_params():
    e1 = _make_entry("GET", "/api/foo", query={"page": "1"}, entry_id="a")
    e2 = _make_entry("GET", "/api/foo", query={"page": "2"}, entry_id="b")
    result = dedupe([e1, e2])
    assert len(result) == 2


def test_dedupe_empty_list():
    assert dedupe([]) == []


def test_find_duplicates_groups_correctly():
    e1 = _make_entry("GET", "/api/foo", entry_id="a")
    e2 = _make_entry("GET", "/api/foo", entry_id="b")
    e3 = _make_entry("POST", "/api/bar", entry_id="c")
    groups = find_duplicates([e1, e2, e3])
    assert len(groups) == 1
    assert len(groups[0]) == 2


def test_find_duplicates_returns_empty_when_no_dupes():
    e1 = _make_entry("GET", "/api/foo", entry_id="a")
    e2 = _make_entry("POST", "/api/bar", entry_id="b")
    groups = find_duplicates([e1, e2])
    assert groups == []


def test_count_unique_all_unique():
    e1 = _make_entry("GET", "/api/foo", entry_id="a")
    e2 = _make_entry("GET", "/api/bar", entry_id="b")
    assert count_unique([e1, e2]) == 2


def test_count_unique_with_duplicates():
    e1 = _make_entry("GET", "/api/foo", entry_id="a")
    e2 = _make_entry("GET", "/api/foo", entry_id="b")
    e3 = _make_entry("GET", "/api/foo", entry_id="c")
    assert count_unique([e1, e2, e3]) == 1


def test_has_duplicates_true():
    e1 = _make_entry("GET", "/api/foo", entry_id="a")
    e2 = _make_entry("GET", "/api/foo", entry_id="b")
    assert has_duplicates([e1, e2]) is True


def test_has_duplicates_false():
    e1 = _make_entry("GET", "/api/foo", entry_id="a")
    e2 = _make_entry("POST", "/api/foo", entry_id="b")
    assert has_duplicates([e1, e2]) is False
