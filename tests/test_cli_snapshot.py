"""Tests for reqtrace.cli_snapshot CLI commands."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from reqtrace.cli_snapshot import build_snapshot_parser, run_snapshot
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.snapshot import save_snapshot
from reqtrace.storage import TraceStore


def _make_entry(method="GET", url="http://example.com/ping", status=200):
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    resp = HttpResponse(status_code=status, headers={}, body=None)
    return TraceEntry(request=req, response=resp)


def _store_with(*entries):
    store = TraceStore()
    for e in entries:
        store._entries[e.id] = e
    return store


def test_save_command_writes_file(tmp_path):
    store = _store_with(_make_entry(), _make_entry(method="POST"))
    out_file = str(tmp_path / "out.json")
    parser = build_snapshot_parser()
    args = parser.parse_args(["save", out_file])
    buf = io.StringIO()
    run_snapshot(args, store, out=buf)
    assert Path(out_file).exists()
    assert "2 entries" in buf.getvalue()


def test_load_command_prints_entries(tmp_path):
    e = _make_entry(url="http://example.com/items")
    store = _store_with(e)
    snap = tmp_path / "snap.json"
    save_snapshot(store, snap)
    parser = build_snapshot_parser()
    args = parser.parse_args(["load", str(snap)])
    buf = io.StringIO()
    run_snapshot(args, TraceStore(), out=buf)
    output = buf.getvalue()
    assert "1 entries" in output
    assert "http://example.com/items" in output


def test_merge_command_combines_and_saves(tmp_path):
    e1 = _make_entry(url="http://a.com")
    e2 = _make_entry(url="http://b.com")
    s1 = tmp_path / "s1.json"
    s2 = tmp_path / "s2.json"
    save_snapshot(_store_with(e1), s1)
    save_snapshot(_store_with(e2), s2)
    out = tmp_path / "merged.json"
    parser = build_snapshot_parser()
    args = parser.parse_args(["merge", str(s1), str(s2), "--output", str(out)])
    buf = io.StringIO()
    run_snapshot(args, TraceStore(), out=buf)
    assert out.exists()
    assert "2 unique entries" in buf.getvalue()


def test_no_subcommand_prints_help(tmp_path):
    parser = build_snapshot_parser()
    args = parser.parse_args([])
    buf = io.StringIO()
    run_snapshot(args, TraceStore(), out=buf)
    assert "sub-command" in buf.getvalue()
