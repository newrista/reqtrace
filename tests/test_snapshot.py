"""Tests for reqtrace.snapshot (save, load, merge)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.snapshot import load_snapshot, merge_snapshots, save_snapshot
from reqtrace.storage import TraceStore


def _make_entry(method="GET", url="http://example.com/api", status=200):
    req = HttpRequest(method=method, url=url, headers={"Host": "example.com"}, body=None)
    resp = HttpResponse(status_code=status, headers={"Content-Type": "application/json"}, body='{"ok":true}')
    entry = TraceEntry(request=req, response=resp)
    entry.tags = {"test"}
    entry.metadata = {"note": "hello"}
    return entry


def _store_with(*entries):
    store = TraceStore()
    for e in entries:
        store._entries[e.id] = e
    return store


def test_save_creates_valid_json(tmp_path):
    store = _store_with(_make_entry(), _make_entry(method="POST", status=201))
    out = tmp_path / "snap.json"
    save_snapshot(store, out)
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    assert len(data) == 2


def test_save_round_trip_preserves_fields(tmp_path):
    entry = _make_entry(method="DELETE", url="http://example.com/item/1", status=204)
    store = _store_with(entry)
    out = tmp_path / "snap.json"
    save_snapshot(store, out)
    loaded = load_snapshot(out)
    restored = loaded.get_by_id(entry.id)
    assert restored is not None
    assert restored.request.method == "DELETE"
    assert restored.request.url == "http://example.com/item/1"
    assert restored.response.status_code == 204


def test_load_preserves_tags_and_metadata(tmp_path):
    entry = _make_entry()
    entry.tags = {"alpha", "beta"}
    entry.metadata = {"env": "staging"}
    store = _store_with(entry)
    out = tmp_path / "snap.json"
    save_snapshot(store, out)
    loaded = load_snapshot(out)
    restored = loaded.get_by_id(entry.id)
    assert "alpha" in restored.tags
    assert "beta" in restored.tags
    assert restored.metadata["env"] == "staging"


def test_load_empty_snapshot(tmp_path):
    out = tmp_path / "empty.json"
    out.write_text("[]", encoding="utf-8")
    store = load_snapshot(out)
    assert store.get_all() == []


def test_merge_combines_entries(tmp_path):
    e1 = _make_entry(url="http://a.com/1")
    e2 = _make_entry(url="http://b.com/2")
    snap1 = tmp_path / "s1.json"
    snap2 = tmp_path / "s2.json"
    save_snapshot(_store_with(e1), snap1)
    save_snapshot(_store_with(e2), snap2)
    merged = merge_snapshots([snap1, snap2])
    assert len(merged.get_all()) == 2


def test_merge_deduplicates_by_id(tmp_path):
    e = _make_entry()
    snap1 = tmp_path / "s1.json"
    snap2 = tmp_path / "s2.json"
    save_snapshot(_store_with(e), snap1)
    save_snapshot(_store_with(e), snap2)
    merged = merge_snapshots([snap1, snap2])
    assert len(merged.get_all()) == 1


def test_save_snapshot_string_path(tmp_path):
    store = _store_with(_make_entry())
    out = str(tmp_path / "snap.json")
    save_snapshot(store, out)
    assert Path(out).exists()
