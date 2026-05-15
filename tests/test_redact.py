"""Tests for reqtrace.redact module."""

import pytest
from reqtrace.redact import (
    redact_headers,
    redact_query_params,
    redact_entry,
    REDACTED,
)
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
import datetime


def _make_entry(req_headers=None, resp_headers=None, query_params=None):
    req = HttpRequest(
        method="GET",
        path="/api/data",
        query_string="token=abc&page=2",
        headers=req_headers or {"Authorization": "Bearer secret", "Accept": "application/json"},
        body=b"",
        content_type="application/json",
        query_params=query_params or {"token": "abc", "page": "2"},
    )
    resp = HttpResponse(
        status_code=200,
        headers=resp_headers or {"Set-Cookie": "session=xyz", "Content-Type": "application/json"},
        body=b'{"ok": true}',
        content_type="application/json",
    )
    return TraceEntry(
        id="test-1",
        timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0),
        request=req,
        response=resp,
    )


def test_redact_headers_sensitive_keys():
    headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}
    result = redact_headers(headers)
    assert result["Authorization"] == REDACTED
    assert result["Content-Type"] == "application/json"


def test_redact_headers_cookie():
    headers = {"Cookie": "session=abc", "X-Api-Key": "key123", "Accept": "*/*"}
    result = redact_headers(headers)
    assert result["Cookie"] == REDACTED
    assert result["X-Api-Key"] == REDACTED
    assert result["Accept"] == "*/*"


def test_redact_headers_custom_patterns():
    import re
    headers = {"X-Custom-Secret": "val", "X-Other": "visible"}
    patterns = [re.compile(r"^x-custom-secret$", re.IGNORECASE)]
    result = redact_headers(headers, patterns=patterns)
    assert result["X-Custom-Secret"] == REDACTED
    assert result["X-Other"] == "visible"


def test_redact_query_params_token():
    params = {"token": "secret", "page": "1", "api_key": "abc"}
    result = redact_query_params(params)
    assert result["token"] == REDACTED
    assert result["api_key"] == REDACTED
    assert result["page"] == "1"


def test_redact_query_params_no_sensitive():
    params = {"page": "2", "limit": "10"}
    result = redact_query_params(params)
    assert result == params


def test_redact_entry_request_headers():
    entry = _make_entry()
    result = redact_entry(entry)
    assert result.request.headers["Authorization"] == REDACTED
    assert result.request.headers["Accept"] == "application/json"


def test_redact_entry_response_headers():
    entry = _make_entry()
    result = redact_entry(entry)
    assert result.response.headers["Set-Cookie"] == REDACTED
    assert result.response.headers["Content-Type"] == "application/json"


def test_redact_entry_query_params():
    entry = _make_entry()
    result = redact_entry(entry)
    assert result.request.query_params["token"] == REDACTED
    assert result.request.query_params["page"] == "2"


def test_redact_entry_preserves_metadata():
    entry = _make_entry()
    result = redact_entry(entry)
    assert result.id == entry.id
    assert result.timestamp == entry.timestamp
    assert result.request.method == "GET"
    assert result.response.status_code == 200
