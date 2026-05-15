"""Tests for reqtrace.diff module."""

import pytest
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.diff import diff_entries, diff_summary


def _make_request(
    method="GET",
    path="/api/v1/items",
    query_string="",
    headers=None,
    body=None,
):
    return HttpRequest(
        method=method,
        path=path,
        query_string=query_string,
        headers=headers or [("content-type", "application/json")],
        body=body,
    )


def _make_response(status_code=200, headers=None, body=b'{"ok": true}'):
    return HttpResponse(
        status_code=status_code,
        headers=headers or [("content-type", "application/json")],
        body=body,
    )


def _make_entry(request=None, response=None, entry_id="abc"):
    return TraceEntry(
        id=entry_id,
        request=request or _make_request(),
        response=response or _make_response(),
    )


def test_diff_identical_entries_is_empty():
    a = _make_entry()
    b = _make_entry()
    assert diff_entries(a, b) == {}


def test_diff_detects_method_change():
    a = _make_entry(request=_make_request(method="GET"))
    b = _make_entry(request=_make_request(method="POST"))
    result = diff_entries(a, b)
    assert "request" in result
    assert result["request"]["method"] == {"before": "GET", "after": "POST"}


def test_diff_detects_path_change():
    a = _make_entry(request=_make_request(path="/old"))
    b = _make_entry(request=_make_request(path="/new"))
    result = diff_entries(a, b)
    assert result["request"]["path"] == {"before": "/old", "after": "/new"}


def test_diff_detects_status_code_change():
    a = _make_entry(response=_make_response(status_code=200))
    b = _make_entry(response=_make_response(status_code=404))
    result = diff_entries(a, b)
    assert "response" in result
    assert result["response"]["status_code"] == {"before": 200, "after": 404}


def test_diff_detects_response_body_change():
    a = _make_entry(response=_make_response(body=b'{"x": 1}'))
    b = _make_entry(response=_make_response(body=b'{"x": 2}'))
    result = diff_entries(a, b)
    assert result["response"]["body"]["before"] == b'{"x": 1}'
    assert result["response"]["body"]["after"] == b'{"x": 2}'


def test_diff_detects_header_change():
    a = _make_entry(request=_make_request(headers=[("accept", "application/json")]))
    b = _make_entry(request=_make_request(headers=[("accept", "text/html")]))
    result = diff_entries(a, b)
    assert "headers" in result["request"]
    assert result["request"]["headers"]["accept"]["before"] == "application/json"


def test_diff_summary_returns_strings():
    a = _make_entry(request=_make_request(method="GET"))
    b = _make_entry(request=_make_request(method="DELETE"))
    delta = diff_entries(a, b)
    lines = diff_summary(delta)
    assert len(lines) == 1
    assert "request.method" in lines[0]
    assert "GET" in lines[0]
    assert "DELETE" in lines[0]


def test_diff_summary_empty_on_no_changes():
    a = _make_entry()
    b = _make_entry()
    assert diff_summary(diff_entries(a, b)) == []
