"""Tests for reqtrace.chain."""

import pytest
from datetime import datetime, timedelta
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.chain import (
    group_by_session,
    group_by_path_prefix,
    find_chains,
    chain_summary,
)


def _make_entry(
    path: str = "/api/resource",
    method: str = "GET",
    status: int = 200,
    timestamp: datetime = None,
    session_id: str = None,
) -> TraceEntry:
    headers = {}
    if session_id:
        headers["X-Session-Id"] = session_id
    req = HttpRequest(
        method=method,
        path=path,
        headers=headers,
        query_params={},
        body=None,
    )
    resp = HttpResponse(
        status_code=status,
        headers={"Content-Type": "application/json"},
        body=None,
    )
    return TraceEntry(
        request=req,
        response=resp,
        timestamp=timestamp or datetime(2024, 1, 1, 12, 0, 0),
    )


def test_group_by_session_known_sessions():
    e1 = _make_entry(session_id="abc")
    e2 = _make_entry(path="/api/other", session_id="abc")
    e3 = _make_entry(path="/api/thing", session_id="xyz")
    result = group_by_session([e1, e2, e3])
    assert set(result.keys()) == {"abc", "xyz"}
    assert len(result["abc"]) == 2
    assert len(result["xyz"]) == 1


def test_group_by_session_unknown_falls_back():
    e1 = _make_entry()  # no session header
    result = group_by_session([e1])
    assert "__unknown__" in result
    assert len(result["__unknown__"]) == 1


def test_group_by_session_case_insensitive():
    req = HttpRequest(method="GET", path="/", headers={"x-session-id": "s1"}, query_params={}, body=None)
    resp = HttpResponse(status_code=200, headers={}, body=None)
    entry = TraceEntry(request=req, response=resp, timestamp=datetime(2024, 1, 1))
    result = group_by_session([entry], session_header="X-Session-Id")
    assert "s1" in result


def test_group_by_path_prefix_depth_1():
    e1 = _make_entry(path="/api/users")
    e2 = _make_entry(path="/api/orders")
    e3 = _make_entry(path="/health")
    result = group_by_path_prefix([e1, e2, e3], depth=1)
    assert "/api" in result
    assert "/health" in result
    assert len(result["/api"]) == 2


def test_group_by_path_prefix_depth_2():
    e1 = _make_entry(path="/api/v1/users")
    e2 = _make_entry(path="/api/v2/users")
    result = group_by_path_prefix([e1, e2], depth=2)
    assert "/api/v1" in result
    assert "/api/v2" in result


def test_find_chains_splits_on_gap():
    base = datetime(2024, 1, 1, 12, 0, 0)
    entries = [
        _make_entry(timestamp=base),
        _make_entry(timestamp=base + timedelta(seconds=1)),
        _make_entry(timestamp=base + timedelta(seconds=10)),  # gap
        _make_entry(timestamp=base + timedelta(seconds=11)),
    ]
    chains = find_chains(entries, gap_seconds=2.0)
    assert len(chains) == 2
    assert len(chains[0]) == 2
    assert len(chains[1]) == 2


def test_find_chains_single_entry():
    e = _make_entry()
    chains = find_chains([e])
    assert len(chains) == 1
    assert chains[0] == [e]


def test_find_chains_empty():
    assert find_chains([]) == []


def test_chain_summary_fields():
    base = datetime(2024, 1, 1, 12, 0, 0)
    chains = [
        [
            _make_entry(path="/a", method="GET", status=200, timestamp=base),
            _make_entry(path="/b", method="POST", status=201, timestamp=base + timedelta(seconds=1)),
        ]
    ]
    summaries = chain_summary(chains)
    assert len(summaries) == 1
    s = summaries[0]
    assert s["chain_index"] == 0
    assert s["length"] == 2
    assert s["duration_seconds"] == 1.0
    assert s["methods"] == ["GET", "POST"]
    assert s["paths"] == ["/a", "/b"]
    assert s["statuses"] == [200, 201]
