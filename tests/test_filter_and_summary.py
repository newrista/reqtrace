"""Tests for reqtrace.filter and reqtrace.summary modules."""

import pytest
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.filter import (
    filter_by_method,
    filter_by_path,
    filter_by_status,
    filter_by_status_range,
    filter_by_content_type,
    search_entries,
)
from reqtrace.summary import summarize, top_paths


def _make_entry(method="GET", path="/api", status=200, content_type=None):
    req = HttpRequest(
        method=method,
        path=path,
        query_string="",
        headers={},
        body=None,
        content_type=content_type,
    )
    resp = HttpResponse(status_code=status, headers={}, body=None)
    return TraceEntry(request=req, response=resp)


def test_filter_by_method():
    entries = [_make_entry("GET"), _make_entry("POST"), _make_entry("get")]
    result = filter_by_method(entries, "get")
    assert len(result) == 2


def test_filter_by_path():
    entries = [_make_entry(path="/api/users"), _make_entry(path="/health")]
    result = filter_by_path(entries, "/api")
    assert len(result) == 1
    assert result[0].request.path == "/api/users"


def test_filter_by_status():
    entries = [_make_entry(status=200), _make_entry(status=404), _make_entry(status=200)]
    result = filter_by_status(entries, 200)
    assert len(result) == 2


def test_filter_by_status_range():
    entries = [_make_entry(status=200), _make_entry(status=404), _make_entry(status=500)]
    result = filter_by_status_range(entries, 400, 499)
    assert len(result) == 1
    assert result[0].response.status_code == 404


def test_filter_by_content_type():
    entries = [
        _make_entry(content_type="application/json"),
        _make_entry(content_type="text/html"),
        _make_entry(content_type=None),
    ]
    result = filter_by_content_type(entries, "json")
    assert len(result) == 1


def test_search_entries_combined():
    entries = [
        _make_entry("POST", "/api/items", 201, "application/json"),
        _make_entry("GET", "/api/items", 200),
        _make_entry("POST", "/health", 200),
    ]
    result = search_entries(entries, method="POST", path_prefix="/api")
    assert len(result) == 1
    assert result[0].response.status_code == 201


def test_summarize_empty():
    s = summarize([])
    assert s["total"] == 0
    assert s["error_rate"] == 0.0


def test_summarize_counts():
    entries = [
        _make_entry("GET", status=200),
        _make_entry("POST", status=201),
        _make_entry("GET", status=500),
    ]
    s = summarize(entries)
    assert s["total"] == 3
    assert s["methods"]["GET"] == 2
    assert s["methods"]["POST"] == 1
    assert abs(s["error_rate"] - round(1 / 3, 4)) < 1e-6


def test_top_paths():
    entries = [
        _make_entry(path="/a"),
        _make_entry(path="/a"),
        _make_entry(path="/b"),
    ]
    result = top_paths(entries, n=2)
    assert result[0]["path"] == "/a"
    assert result[0]["count"] == 2
