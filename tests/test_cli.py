"""Tests for the reqtrace CLI module."""

import json
import pytest
from unittest.mock import patch
from reqtrace.storage import TraceStore
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.cli import run


def _make_entry(method="GET", path="/api", status=200):
    req = HttpRequest(
        method=method, path=path, query_string="",
        headers={}, body=None, content_type=None,
    )
    resp = HttpResponse(status_code=status, headers={}, body=None)
    return TraceEntry(request=req, response=resp)


@pytest.fixture
def store_with_entries():
    store = TraceStore()
    store.add(_make_entry("GET", "/api/users", 200))
    store.add(_make_entry("POST", "/api/users", 201))
    store.add(_make_entry("GET", "/health", 404))
    return store


def test_summary_command(store_with_entries, capsys):
    rc = run(store_with_entries, ["summary"])
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["total"] == 3
    assert "GET" in data["methods"]


def test_top_paths_command(store_with_entries, capsys):
    rc = run(store_with_entries, ["top-paths", "--n", "2"])
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) <= 2


def test_filter_command_by_method(store_with_entries, capsys):
    rc = run(store_with_entries, ["filter", "--method", "POST"])
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data) == 1


def test_export_command_json(store_with_entries, capsys):
    rc = run(store_with_entries, ["export", "--format", "json"])
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)


def test_no_command_returns_nonzero(capsys):
    store = TraceStore()
    rc = run(store, [])
    assert rc == 1


def test_export_to_file(store_with_entries, tmp_path):
    out_file = tmp_path / "traces.json"
    rc = run(store_with_entries, ["export", "--format", "json", "--output", str(out_file)])
    assert rc == 0
    content = out_file.read_text()
    data = json.loads(content)
    assert len(data) == 3
