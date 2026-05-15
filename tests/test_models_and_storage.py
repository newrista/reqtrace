"""Tests for reqtrace models and storage."""

import pytest
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.storage import TraceStore


def make_request(method="GET", url="http://example.com/path?q=1",
                 headers=None, body=None) -> HttpRequest:
    return HttpRequest(
        method=method,
        url=url,
        headers=headers or {},
        body=body,
        query_params={"q": "1"} if "?" in url else {},
    )


def make_response(status=200, headers=None, body=None) -> HttpResponse:
    return HttpResponse(
        status_code=status,
        headers=headers or {},
        body=body,
    )


def make_entry(entry_id="abc", method="GET", status=200, tags=None) -> TraceEntry:
    return TraceEntry(
        id=entry_id,
        request=make_request(method=method),
        response=make_response(status=status),
        timestamp="2024-01-01T00:00:00Z",
        tags=list(tags or []),
    )


def test_request_path_and_query():
    req = make_request(url="http://example.com/api/v1?foo=bar")
    assert req.path == "/api/v1"


def test_request_content_type():
    req = make_request(headers={"Content-Type": "application/json"})
    assert req.is_json()


def test_request_has_body():
    req = make_request(body=b'{"key": "value"}')
    assert req.has_body()


def test_request_no_body():
    req = make_request()
    assert not req.has_body()


def test_response_is_success():
    resp = make_response(status=201)
    assert resp.is_success()


def test_response_not_success():
    resp = make_response(status=404)
    assert not resp.is_success()


def test_response_is_json():
    resp = make_response(headers={"Content-Type": "application/json; charset=utf-8"})
    assert resp.is_json()


def test_trace_entry_replace():
    entry = make_entry()
    updated = entry._replace(tags=["new-tag"])
    assert updated.tags == ["new-tag"]
    assert entry.tags == []


def test_store_add_and_get_all():
    store = TraceStore()
    e1 = make_entry("1")
    e2 = make_entry("2")
    store.add(e1)
    store.add(e2)
    all_entries = store.get_all()
    assert len(all_entries) == 2


def test_store_get_by_id():
    store = TraceStore()
    entry = make_entry("xyz")
    store.add(entry)
    found = store.get_by_id("xyz")
    assert found is not None
    assert found.id == "xyz"


def test_store_get_by_id_missing():
    store = TraceStore()
    assert store.get_by_id("missing") is None


def test_store_clear():
    store = TraceStore()
    store.add(make_entry("1"))
    store.clear()
    assert store.get_all() == []
