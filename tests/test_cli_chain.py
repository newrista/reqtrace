"""Tests for reqtrace.cli_chain."""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from io import StringIO
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.storage import TraceStore
from reqtrace.cli_chain import build_chain_parser, run_chain


def _make_entry(
    path="/api/items",
    method="GET",
    status=200,
    timestamp=None,
    session_id=None,
):
    headers = {}
    if session_id:
        headers["X-Session-Id"] = session_id
    req = HttpRequest(method=method, path=path, headers=headers, query_params={}, body=None)
    resp = HttpResponse(status_code=status, headers={}, body=None)
    return TraceEntry(
        request=req,
        response=resp,
        timestamp=timestamp or datetime(2024, 6, 1, 10, 0, 0),
    )


@pytest.fixture
def store_with_entries():
    store = TraceStore()
    store.add(_make_entry(path="/api/users", session_id="s1"))
    store.add(_make_entry(path="/api/orders", session_id="s1"))
    store.add(_make_entry(path="/api/products", session_id="s2"))
    return store


def test_session_command_counts(store_with_entries, capsys):
    parser = build_chain_parser()
    args = parser.parse_args(["session", "--header", "X-Session-Id"])
    run_chain(store_with_entries, args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["s1"] == 2
    assert data["s2"] == 1


def test_prefix_command_groups(store_with_entries, capsys):
    parser = build_chain_parser()
    args = parser.parse_args(["prefix", "--depth", "1"])
    run_chain(store_with_entries, args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "/api" in data
    assert data["/api"] == 3


def test_detect_command_returns_summaries(capsys):
    base = datetime(2024, 6, 1, 10, 0, 0)
    store = TraceStore()
    store.add(_make_entry(timestamp=base))
    store.add(_make_entry(timestamp=base + timedelta(seconds=1)))
    store.add(_make_entry(timestamp=base + timedelta(seconds=30)))  # gap
    parser = build_chain_parser()
    args = parser.parse_args(["detect", "--gap", "2.0"])
    run_chain(store, args)
    captured = capsys.readouterr()
    summaries = json.loads(captured.out)
    assert len(summaries) == 2
    assert summaries[0]["length"] == 2
    assert summaries[1]["length"] == 1


def test_no_subcommand_prints_help(capsys):
    store = TraceStore()
    parser = build_chain_parser()
    args = parser.parse_args([])
    run_chain(store, args)
    captured = capsys.readouterr()
    assert "chain_cmd" in captured.out or "sub-command" in captured.out
