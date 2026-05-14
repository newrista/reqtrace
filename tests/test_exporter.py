"""Tests for reqtrace.exporter — JSON and HAR export functionality."""

import json
from datetime import datetime, timezone

import pytest

from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.exporter import export_json, export_har


def _make_entry(
    method="GET",
    url="http://example.com/api/items?page=1",
    status_code=200,
    req_body=None,
    resp_body='{"items": []}',
    elapsed_ms=42.5,
) -> TraceEntry:
    request = HttpRequest(
        method=method,
        url=url,
        headers={"Accept": "application/json"},
        body=req_body,
        content_type="application/json" if req_body else None,
    )
    response = HttpResponse(
        status_code=status_code,
        headers={"Content-Type": "application/json"},
        body=resp_body,
        content_type="application/json",
        elapsed_ms=elapsed_ms,
    )
    return TraceEntry(
        id="test-id-001",
        timestamp=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        request=request,
        response=response,
    )


def test_export_json_returns_valid_json():
    entry = _make_entry()
    result = export_json([entry])
    parsed = json.loads(result)
    assert isinstance(parsed, list)
    assert len(parsed) == 1


def test_export_json_fields():
    entry = _make_entry()
    parsed = json.loads(export_json([entry]))
    record = parsed[0]
    assert record["id"] == "test-id-001"
    assert record["request"]["method"] == "GET"
    assert record["request"]["path"] == "/api/items"
    assert record["response"]["status_code"] == 200
    assert record["response"]["elapsed_ms"] == 42.5


def test_export_json_empty_list():
    result = export_json([])
    assert json.loads(result) == []


def test_export_har_structure():
    entry = _make_entry()
    result = export_har([entry])
    har = json.loads(result)
    assert "log" in har
    assert har["log"]["version"] == "1.2"
    assert har["log"]["creator"]["name"] == "reqtrace"
    assert len(har["log"]["entries"]) == 1


def test_export_har_entry_fields():
    entry = _make_entry()
    har = json.loads(export_har([entry]))
    har_entry = har["log"]["entries"][0]
    assert har_entry["request"]["method"] == "GET"
    assert har_entry["request"]["url"] == "http://example.com/api/items?page=1"
    assert har_entry["response"]["status"] == 200
    assert har_entry["timings"]["wait"] == 42.5


def test_export_har_query_string():
    entry = _make_entry()
    har = json.loads(export_har([entry]))
    qs = har["log"]["entries"][0]["request"]["queryString"]
    assert isinstance(qs, list)


def test_export_har_post_data():
    entry = _make_entry(
        method="POST",
        url="http://example.com/api/items",
        req_body='{"name": "widget"}',
    )
    har = json.loads(export_har([entry]))
    post_data = har["log"]["entries"][0]["request"]["postData"]
    assert post_data is not None
    assert post_data["text"] == '{"name": "widget"}'


def test_export_har_multiple_entries():
    entries = [_make_entry(), _make_entry(method="POST", url="http://example.com/api/items")]
    har = json.loads(export_har(entries))
    assert len(har["log"]["entries"]) == 2
