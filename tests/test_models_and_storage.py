"""Tests for reqtrace core models and in-memory storage."""

import time
from datetime import datetime

import pytest

from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.storage import TraceStore


# --- HttpRequest ---

def make_request(**kwargs) -> HttpRequest:
    defaults = {"method": "GET", "url": "http://example.com/api/v1"}
    defaults.update(kwargs)
    return HttpRequest(**defaults)


def make_response(**kwargs) -> HttpResponse:
    defaults = {"status_code": 200}
    defaults.update(kwargs)
    return HttpResponse(**defaults)


def make_entry(duration_ms: float = 42.0) -> TraceEntry:
    return TraceEntry(request=make_request(), response=make_response(), duration_ms=duration_ms)


def test_request_path_and_query():
    req = make_request(url="http://example.com/api/v1?foo=bar&baz=1")
    assert req.path == "/api/v1"
    assert req.query_string == "foo=bar&baz=1"


def test_request_content_type():
    req = make_request(headers={"content-type": "application/json"})
    assert req.content_type() == "application/json"


def test_response_is_success():
    assert make_response(status_code=200).is_success
    assert make_response(status_code=201).is_success
    assert not make_response(status_code=404).is_success
    assert not make_response(status_code=500).is_success


def test_trace_entry_auto_id():
    entry = make_entry()
    assert entry.trace_id != ""


def test_trace_entry_to_dict():
    req = make_request(body=b"{\"key\": \"value\"}")
    resp = make_response(status_code=201, body=b"created")
    entry = TraceEntry(request=req, response=resp, duration_ms=10.5)
    d = entry.to_dict()
    assert d["duration_ms"] == 10.5
    assert d["request"]["method"] == "GET"
    assert d["response"]["status_code"] == 201
    assert d["response"]["body"] == "created"


# --- TraceStore ---

def test_store_add_and_len():
    store = TraceStore()
    store.add(make_entry())
    store.add(make_entry())
    assert len(store) == 2


def test_store_max_entries():
    store = TraceStore(max_entries=3)
    for _ in range(5):
        store.add(make_entry())
    assert len(store) == 3


def test_store_get_by_id():
    store = TraceStore()
    entry = make_entry()
    store.add(entry)
    found = store.get_by_id(entry.trace_id)
    assert found is entry
    assert store.get_by_id("nonexistent") is None


def test_store_filter_by_method():
    store = TraceStore()
    store.add(TraceEntry(request=make_request(method="GET"), response=make_response(), duration_ms=1))
    store.add(TraceEntry(request=make_request(method="POST"), response=make_response(), duration_ms=2))
    assert len(store.filter_by_method("GET")) == 1
    assert len(store.filter_by_method("post")) == 1


def test_store_filter_by_status():
    store = TraceStore()
    store.add(TraceEntry(request=make_request(), response=make_response(status_code=200), duration_ms=1))
    store.add(TraceEntry(request=make_request(), response=make_response(status_code=404), duration_ms=2))
    assert len(store.filter_by_status(200)) == 1
    assert len(store.filter_by_status(500)) == 0


def test_store_clear():
    store = TraceStore()
    store.add(make_entry())
    store.clear()
    assert len(store) == 0
