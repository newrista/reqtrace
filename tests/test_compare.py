"""Tests for reqtrace.compare module."""

import pytest
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.compare import compare_by_index, compare_by_path_method, changed_only


def _req(method="GET", path="/items", status=200, resp_body=b'{}'):
    request = HttpRequest(
        method=method,
        path=path,
        query_string="",
        headers=[("content-type", "application/json")],
        body=None,
    )
    response = HttpResponse(
        status_code=status,
        headers=[("content-type", "application/json")],
        body=resp_body,
    )
    return request, response


def _entry(entry_id, method="GET", path="/items", status=200, resp_body=b'{}'):
    req, resp = _req(method=method, path=path, status=status, resp_body=resp_body)
    return TraceEntry(id=entry_id, request=req, response=resp)


def test_compare_by_index_no_changes():
    a = [_entry("1"), _entry("2")]
    b = [_entry("3"), _entry("4")]
    results = compare_by_index(a, b)
    assert len(results) == 2
    assert all(r["changed"] is False for r in results)


def test_compare_by_index_detects_change():
    a = [_entry("1", status=200)]
    b = [_entry("2", status=500)]
    results = compare_by_index(a, b)
    assert results[0]["changed"] is True
    assert "response" in results[0]["diff"]


def test_compare_by_index_pairs_by_position():
    a = [_entry("a1"), _entry("a2")]
    b = [_entry("b1"), _entry("b2")]
    results = compare_by_index(a, b)
    assert results[0]["id_a"] == "a1"
    assert results[0]["id_b"] == "b1"
    assert results[1]["id_a"] == "a2"


def test_compare_by_index_stops_at_shorter_list():
    a = [_entry("1"), _entry("2"), _entry("3")]
    b = [_entry("4")]
    results = compare_by_index(a, b)
    assert len(results) == 1


def test_compare_by_path_method_matches_correctly():
    a = [_entry("a1", method="GET", path="/users")]
    b = [_entry("b1", method="GET", path="/users", status=404)]
    results = compare_by_path_method(a, b)
    assert len(results) == 1
    assert results[0]["changed"] is True
    assert results[0]["key"] == "GET /users"


def test_compare_by_path_method_unmatched_entry():
    a = [_entry("a1", method="DELETE", path="/items/1")]
    b = [_entry("b1", method="GET", path="/items")]
    results = compare_by_path_method(a, b)
    assert results[0]["id_b"] is None
    assert "no matching" in results[0]["summary"][0]


def test_changed_only_filters_unchanged():
    a = [_entry("1", status=200), _entry("2", status=200)]
    b = [_entry("3", status=200), _entry("4", status=500)]
    comparison = compare_by_index(a, b)
    changed = changed_only(comparison)
    assert len(changed) == 1
    assert changed[0]["index"] == 1


def test_compare_summary_populated_on_change():
    a = [_entry("1", path="/a")]
    b = [_entry("2", path="/b")]
    results = compare_by_index(a, b)
    assert len(results[0]["summary"]) > 0
