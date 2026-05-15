"""Tests for reqtrace.assert_response module."""

import pytest
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.assert_response import (
    assert_status,
    assert_header_present,
    assert_header_value,
    assert_body_contains,
    assert_all,
    all_passed,
)


def _make_entry(
    status: int = 200,
    headers: dict = None,
    body: str = "",
) -> TraceEntry:
    req = HttpRequest(
        method="GET",
        url="http://example.com/api/test",
        headers={},
        body=None,
    )
    resp = HttpResponse(
        status_code=status,
        headers=headers or {"Content-Type": "application/json"},
        body=body,
    )
    return TraceEntry(request=req, response=resp)


def test_assert_status_passes():
    entry = _make_entry(status=200)
    result = assert_status(entry, 200)
    assert result.passed is True
    assert "200" in result.message


def test_assert_status_fails():
    entry = _make_entry(status=404)
    result = assert_status(entry, 200)
    assert result.passed is False
    assert "404" in result.message
    assert "200" in result.message


def test_assert_header_present_passes():
    entry = _make_entry(headers={"X-Request-Id": "abc123"})
    result = assert_header_present(entry, "X-Request-Id")
    assert result.passed is True


def test_assert_header_present_case_insensitive():
    entry = _make_entry(headers={"Content-Type": "application/json"})
    result = assert_header_present(entry, "content-type")
    assert result.passed is True


def test_assert_header_present_fails():
    entry = _make_entry(headers={})
    result = assert_header_present(entry, "Authorization")
    assert result.passed is False
    assert "Authorization" in result.message


def test_assert_header_value_passes():
    entry = _make_entry(headers={"Content-Type": "application/json"})
    result = assert_header_value(entry, "Content-Type", "application/json")
    assert result.passed is True


def test_assert_header_value_fails_wrong_value():
    entry = _make_entry(headers={"Content-Type": "text/plain"})
    result = assert_header_value(entry, "Content-Type", "application/json")
    assert result.passed is False
    assert "text/plain" in result.message


def test_assert_body_contains_passes():
    entry = _make_entry(body='{"status": "ok"}')
    result = assert_body_contains(entry, '"status"')
    assert result.passed is True


def test_assert_body_contains_fails():
    entry = _make_entry(body="hello world")
    result = assert_body_contains(entry, "missing")
    assert result.passed is False
    assert "missing" in result.message


def test_assert_body_contains_none_body():
    entry = _make_entry(body=None)
    result = assert_body_contains(entry, "anything")
    assert result.passed is False


def test_assert_all_all_pass():
    entry = _make_entry(
        status=201,
        headers={"Content-Type": "application/json"},
        body='{"id": 1}',
    )
    results = assert_all(
        entry,
        status=201,
        headers_present=["Content-Type"],
        body_contains='"id"',
    )
    assert len(results) == 3
    assert all_passed(results) is True


def test_assert_all_partial_failure():
    entry = _make_entry(status=500, body="error")
    results = assert_all(entry, status=200, body_contains="success")
    assert all_passed(results) is False
    failures = [r for r in results if not r.passed]
    assert len(failures) == 2


def test_assert_all_no_assertions():
    entry = _make_entry()
    results = assert_all(entry)
    assert results == []
    assert all_passed(results) is True


def test_result_carries_entry_id():
    entry = _make_entry(status=200)
    result = assert_status(entry, 200)
    assert result.entry_id == entry.id
