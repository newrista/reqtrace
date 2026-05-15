"""Tests for reqtrace.timeline module."""

import pytest
from datetime import datetime, timedelta
from reqtrace.timeline import (
    sort_by_time,
    entries_in_range,
    slowest,
    timeline_summary,
)
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry


def _make_entry(entry_id: str, offset_seconds: int = 0, duration: float = None) -> TraceEntry:
    ts = datetime(2024, 1, 1, 12, 0, 0) + timedelta(seconds=offset_seconds)
    req = HttpRequest(method="GET", url="http://example.com/api")
    resp = HttpResponse(status_code=200)
    return TraceEntry(id=entry_id, request=req, response=resp, timestamp=ts, duration=duration)


def test_sort_by_time_ascending():
    entries = [_make_entry("c", 20), _make_entry("a", 0), _make_entry("b", 10)]
    result = sort_by_time(entries)
    assert [e.id for e in result] == ["a", "b", "c"]


def test_sort_by_time_descending():
    entries = [_make_entry("a", 0), _make_entry("b", 10), _make_entry("c", 20)]
    result = sort_by_time(entries, reverse=True)
    assert [e.id for e in result] == ["c", "b", "a"]


def test_entries_in_range_filters_correctly():
    entries = [
        _make_entry("a", 0),
        _make_entry("b", 30),
        _make_entry("c", 60),
    ]
    start = datetime(2024, 1, 1, 12, 0, 10)
    end = datetime(2024, 1, 1, 12, 0, 50)
    result = entries_in_range(entries, start, end)
    assert len(result) == 1
    assert result[0].id == "b"


def test_entries_in_range_inclusive_bounds():
    entries = [_make_entry("a", 0), _make_entry("b", 10)]
    start = datetime(2024, 1, 1, 12, 0, 0)
    end = datetime(2024, 1, 1, 12, 0, 10)
    result = entries_in_range(entries, start, end)
    assert len(result) == 2


def test_slowest_returns_top_n():
    entries = [
        _make_entry("fast", duration=50.0),
        _make_entry("slow", duration=300.0),
        _make_entry("medium", duration=150.0),
        _make_entry("no_duration"),
    ]
    result = slowest(entries, n=2)
    assert len(result) == 2
    assert result[0].id == "slow"
    assert result[1].id == "medium"


def test_slowest_excludes_entries_without_duration():
    entries = [_make_entry("a"), _make_entry("b")]
    result = slowest(entries)
    assert result == []


def test_timeline_summary_empty():
    result = timeline_summary([])
    assert result["count"] == 0
    assert result["earliest"] is None
    assert result["latest"] is None
    assert result["span_seconds"] is None


def test_timeline_summary_single_entry():
    entries = [_make_entry("a", 0, duration=100.0)]
    result = timeline_summary(entries)
    assert result["count"] == 1
    assert result["span_seconds"] == 0.0
    assert result["avg_duration_ms"] == 100.0


def test_timeline_summary_multiple_entries():
    entries = [
        _make_entry("a", 0, duration=100.0),
        _make_entry("b", 10, duration=200.0),
        _make_entry("c", 30),
    ]
    result = timeline_summary(entries)
    assert result["count"] == 3
    assert result["span_seconds"] == 30.0
    assert result["avg_duration_ms"] == 150.0


def test_timeline_summary_no_durations():
    entries = [_make_entry("a", 0), _make_entry("b", 5)]
    result = timeline_summary(entries)
    assert result["avg_duration_ms"] is None
