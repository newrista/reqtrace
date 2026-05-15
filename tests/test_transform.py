"""Tests for reqtrace.transform module."""

import pytest
from datetime import datetime
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.transform import (
    set_request_header,
    remove_request_header,
    set_response_header,
    replace_request_body,
    apply_transforms,
)


def _make_entry(
    method="GET",
    url="http://example.com/api/users",
    req_headers=None,
    req_body=None,
    status=200,
    resp_headers=None,
    resp_body=b"{}",
):
    request = HttpRequest(
        method=method,
        url=url,
        headers=req_headers or {"Content-Type": "application/json"},
        body=req_body,
    )
    response = HttpResponse(
        status_code=status,
        headers=resp_headers or {"Content-Type": "application/json"},
        body=resp_body,
    )
    return TraceEntry(
        id="test-id",
        request=request,
        response=response,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        metadata={},
        tags=[],
    )


def test_set_request_header_adds_new_header():
    entry = _make_entry(req_headers={})
    result = set_request_header(entry, "X-Custom", "value")
    assert result.request.headers["X-Custom"] == "value"


def test_set_request_header_overwrites_existing():
    entry = _make_entry(req_headers={"Authorization": "old"})
    result = set_request_header(entry, "Authorization", "new")
    assert result.request.headers["Authorization"] == "new"


def test_set_request_header_does_not_mutate_original():
    entry = _make_entry(req_headers={"X-Foo": "bar"})
    set_request_header(entry, "X-Foo", "baz")
    assert entry.request.headers["X-Foo"] == "bar"


def test_remove_request_header_removes_existing():
    entry = _make_entry(req_headers={"Authorization": "secret", "Accept": "*/*"})
    result = remove_request_header(entry, "Authorization")
    assert "Authorization" not in result.request.headers
    assert "Accept" in result.request.headers


def test_remove_request_header_case_insensitive():
    entry = _make_entry(req_headers={"Content-Type": "application/json"})
    result = remove_request_header(entry, "content-type")
    assert "Content-Type" not in result.request.headers


def test_remove_request_header_missing_is_noop():
    entry = _make_entry(req_headers={"Accept": "*/*"})
    result = remove_request_header(entry, "X-Missing")
    assert result.request.headers == {"Accept": "*/*"}


def test_set_response_header_adds_header():
    entry = _make_entry(resp_headers={})
    result = set_response_header(entry, "X-Trace-Id", "abc123")
    assert result.response.headers["X-Trace-Id"] == "abc123"


def test_set_response_header_no_response_returns_entry_unchanged():
    entry = _make_entry()
    entry_no_resp = TraceEntry(
        id=entry.id,
        request=entry.request,
        response=None,
        timestamp=entry.timestamp,
        metadata=entry.metadata,
        tags=entry.tags,
    )
    result = set_response_header(entry_no_resp, "X-Foo", "bar")
    assert result.response is None


def test_replace_request_body_sets_new_body():
    entry = _make_entry(req_body=b"old body")
    result = replace_request_body(entry, b"new body")
    assert result.request.body == b"new body"


def test_replace_request_body_with_none():
    entry = _make_entry(req_body=b"some data")
    result = replace_request_body(entry, None)
    assert result.request.body is None


def test_apply_transforms_applies_in_order():
    entry = _make_entry(req_headers={})
    transforms = [
        lambda e: set_request_header(e, "X-Step", "1"),
        lambda e: set_request_header(e, "X-Step", "2"),
    ]
    result = apply_transforms(entry, transforms)
    assert result.request.headers["X-Step"] == "2"


def test_apply_transforms_empty_list_returns_unchanged():
    entry = _make_entry(req_headers={"X-Original": "yes"})
    result = apply_transforms(entry, [])
    assert result.request.headers["X-Original"] == "yes"
