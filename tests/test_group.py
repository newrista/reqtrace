"""Tests for reqtrace.group module."""

import pytest
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.group import (
    group_by_method,
    group_by_path,
    group_by_status,
    group_by_status_class,
    group_by_host,
    group_by,
)


def _make_entry(method="GET", path="/api", status=200, host="example.com"):
    req = HttpRequest(
        method=method,
        url=f"http://{host}{path}",
        headers={"host": host},
        body=None,
    )
    resp = HttpResponse(
        status_code=status,
        headers={"content-type": "application/json"},
        body=b"{}",
    )
    return TraceEntry(request=req, response=resp)


def test_group_by_method_separates_methods():
    entries = [_make_entry("GET"), _make_entry("POST"), _make_entry("GET")]
    result = group_by_method(entries)
    assert set(result.keys()) == {"GET", "POST"}
    assert len(result["GET"]) == 2
    assert len(result["POST"]) == 1


def test_group_by_method_empty():
    assert group_by_method([]) == {}


def test_group_by_path_separates_paths():
    entries = [_make_entry(path="/a"), _make_entry(path="/b"), _make_entry(path="/a")]
    result = group_by_path(entries)
    assert "/a" in result and "/b" in result
    assert len(result["/a"]) == 2


def test_group_by_status_separates_codes():
    entries = [_make_entry(status=200), _make_entry(status=404), _make_entry(status=200)]
    result = group_by_status(entries)
    assert set(result.keys()) == {200, 404}
    assert len(result[200]) == 2


def test_group_by_status_skips_entries_without_response():
    req = HttpRequest(method="GET", url="http://x.com/", headers={}, body=None)
    entry_no_resp = TraceEntry(request=req, response=None)
    entries = [_make_entry(status=200), entry_no_resp]
    result = group_by_status(entries)
    assert list(result.keys()) == [200]


def test_group_by_status_class():
    entries = [
        _make_entry(status=200),
        _make_entry(status=201),
        _make_entry(status=404),
        _make_entry(status=500),
    ]
    result = group_by_status_class(entries)
    assert "2xx" in result
    assert "4xx" in result
    assert "5xx" in result
    assert len(result["2xx"]) == 2


def test_group_by_host():
    entries = [
        _make_entry(host="api.example.com"),
        _make_entry(host="other.com"),
        _make_entry(host="api.example.com"),
    ]
    result = group_by_host(entries)
    assert "api.example.com" in result
    assert len(result["api.example.com"]) == 2


def test_group_by_custom_key_fn():
    entries = [_make_entry(status=200), _make_entry(status=201), _make_entry(status=404)]
    result = group_by(entries, lambda e: e.response.status_code >= 400)
    assert True in result
    assert False in result
    assert len(result[True]) == 1
    assert len(result[False]) == 2
