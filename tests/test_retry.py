"""Tests for reqtrace.retry module."""

import pytest
from datetime import datetime, timezone
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.retry import (
    group_by_request,
    find_retries,
    has_retries,
    retry_summary,
    successful_after_retry,
)


def _make_entry(method="GET", path="/api/data", host="example.com", status=200, ts=None):
    req = HttpRequest(
        method=method,
        url=f"http://{host}{path}",
        headers={"host": host},
        body=None,
    )
    resp = HttpResponse(status_code=status, headers={}, body=None)
    return TraceEntry(
        request=req,
        response=resp,
        timestamp=ts or datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


def test_group_by_request_single_entry():
    entry = _make_entry()
    groups = group_by_request([entry])
    assert len(groups) == 1
    key = ("GET", "example.com", "/api/data")
    assert key in groups
    assert groups[key] == [entry]


def test_group_by_request_groups_same_requests():
    e1 = _make_entry()
    e2 = _make_entry(status=500)
    groups = group_by_request([e1, e2])
    assert len(groups) == 1
    assert len(list(groups.values())[0]) == 2


def test_group_by_request_separates_different_paths():
    e1 = _make_entry(path="/a")
    e2 = _make_entry(path="/b")
    groups = group_by_request([e1, e2])
    assert len(groups) == 2


def test_find_retries_returns_repeated_requests():
    e1 = _make_entry()
    e2 = _make_entry(status=503)
    retries = find_retries([e1, e2])
    assert len(retries) == 1


def test_find_retries_excludes_unique_requests():
    e1 = _make_entry(path="/a")
    e2 = _make_entry(path="/b")
    retries = find_retries([e1, e2])
    assert len(retries) == 0


def test_has_retries_true():
    e1 = _make_entry()
    e2 = _make_entry()
    assert has_retries([e1, e2]) is True


def test_has_retries_false():
    e1 = _make_entry(path="/a")
    e2 = _make_entry(path="/b")
    assert has_retries([e1, e2]) is False


def test_retry_summary_structure():
    e1 = _make_entry(status=500)
    e2 = _make_entry(status=200)
    summary = retry_summary([e1, e2])
    assert len(summary) == 1
    item = summary[0]
    assert item["method"] == "GET"
    assert item["path"] == "/api/data"
    assert item["count"] == 2
    assert 500 in item["status_codes"]
    assert item["has_error"] is True


def test_retry_summary_no_error_when_all_ok():
    e1 = _make_entry(status=200)
    e2 = _make_entry(status=201)
    summary = retry_summary([e1, e2])
    assert summary[0]["has_error"] is False


def test_successful_after_retry_detects_recovery():
    from datetime import timedelta
    base = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    e1 = _make_entry(status=503, ts=base)
    e2 = _make_entry(status=200, ts=base + timedelta(seconds=5))
    result = successful_after_retry([e1, e2])
    assert len(result) == 1
    assert result[0]["final_status"] == 200
    assert result[0]["attempts"] == 2


def test_successful_after_retry_ignores_persistent_failures():
    e1 = _make_entry(status=500)
    e2 = _make_entry(status=503)
    result = successful_after_retry([e1, e2])
    assert result == []
