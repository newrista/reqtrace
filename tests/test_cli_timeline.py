"""Tests for the timeline CLI command."""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from reqtrace.storage import TraceStore
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.cli import run


def _make_entry(entry_id: str, offset: int = 0, duration: float = None) -> TraceEntry:
    ts = datetime(2024, 6, 1, 10, 0, 0) + timedelta(seconds=offset)
    req = HttpRequest(method="GET", url=f"http://api.example.com/items/{entry_id}")
    resp = HttpResponse(status_code=200)
    return TraceEntry(id=entry_id, request=req, response=resp, timestamp=ts, duration=duration)


@pytest.fixture
def store_with_entries():
    store = TraceStore()
    store.add(_make_entry("e1", offset=0, duration=80.0))
    store.add(_make_entry("e2", offset=15, duration=400.0))
    store.add(_make_entry("e3", offset=45, duration=200.0))
    return store


def test_timeline_summary_command(store_with_entries, capsys):
    run(store_with_entries, ["timeline"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["count"] == 3
    assert data["span_seconds"] == 45.0
    assert data["avg_duration_ms"] == pytest.approx(226.67, rel=1e-2)


def test_timeline_slowest_command(store_with_entries, capsys):
    run(store_with_entries, ["timeline", "--slowest", "2"])
    captured = capsys.readouterr()
    lines = [l for l in captured.out.strip().splitlines() if l]
    assert len(lines) == 2
    assert "e2" in lines[0]
    assert "400.0ms" in lines[0]


def test_timeline_empty_store(capsys):
    store = TraceStore()
    run(store, ["timeline"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["count"] == 0
    assert data["earliest"] is None


def test_timeline_slowest_no_duration(capsys):
    store = TraceStore()
    store.add(_make_entry("x1"))  # no duration
    run(store, ["timeline", "--slowest", "3"])
    captured = capsys.readouterr()
    assert captured.out.strip() == ""
