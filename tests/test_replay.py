"""Tests for reqtrace.replay module."""

import pytest
from unittest.mock import MagicMock, patch

from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.storage import TraceStore
from reqtrace.replay import replay_entry, replay_all


def _make_entry(method="GET", url="http://example.com/api/test", status=200):
    req = HttpRequest(
        method=method,
        url=url,
        headers={"Content-Type": "application/json"},
        body="",
    )
    resp = HttpResponse(
        status_code=status,
        headers={"Content-Type": "application/json"},
        body='{"ok": true}',
    )
    return TraceEntry(request=req, response=resp)


def _mock_http_response(status=200, body=b'{"ok": true}', headers=None):
    mock_resp = MagicMock()
    mock_resp.status = status
    mock_resp.read.return_value = body
    mock_resp.getheaders.return_value = list((headers or {"Content-Type": "application/json"}).items())
    return mock_resp


@patch("reqtrace.replay.http.client.HTTPConnection")
def test_replay_entry_success(mock_conn_cls):
    entry = _make_entry()
    mock_conn = MagicMock()
    mock_conn_cls.return_value = mock_conn
    mock_conn.getresponse.return_value = _mock_http_response(status=200)

    result = replay_entry(entry)

    assert result.status_code == 200
    assert result.body == '{"ok": true}'
    mock_conn.request.assert_called_once()
    mock_conn.close.assert_called_once()


@patch("reqtrace.replay.http.client.HTTPSConnection")
def test_replay_entry_https(mock_conn_cls):
    entry = _make_entry(url="https://secure.example.com/api")
    mock_conn = MagicMock()
    mock_conn_cls.return_value = mock_conn
    mock_conn.getresponse.return_value = _mock_http_response(status=201)

    result = replay_entry(entry)

    assert result.status_code == 201
    mock_conn_cls.assert_called_once()


@patch("reqtrace.replay.http.client.HTTPConnection")
def test_replay_entry_override_host(mock_conn_cls):
    entry = _make_entry(url="http://original.host/path")
    mock_conn = MagicMock()
    mock_conn_cls.return_value = mock_conn
    mock_conn.getresponse.return_value = _mock_http_response()

    replay_entry(entry, override_host="localhost:8080")

    mock_conn_cls.assert_called_with("localhost:8080", timeout=10.0)


@patch("reqtrace.replay.http.client.HTTPConnection")
def test_replay_all_status_match(mock_conn_cls):
    store = TraceStore()
    store.add(_make_entry(status=200))
    store.add(_make_entry(status=404))

    mock_conn = MagicMock()
    mock_conn_cls.return_value = mock_conn
    mock_conn.getresponse.return_value = _mock_http_response(status=200)

    results = replay_all(store)

    assert len(results) == 2
    assert results[0]["status_match"] is True
    assert results[1]["status_match"] is False
    assert results[1]["replayed_status"] == 200


@patch("reqtrace.replay.http.client.HTTPConnection")
def test_replay_all_handles_error(mock_conn_cls):
    store = TraceStore()
    store.add(_make_entry())

    mock_conn = MagicMock()
    mock_conn_cls.return_value = mock_conn
    mock_conn.request.side_effect = ConnectionRefusedError("refused")

    results = replay_all(store)

    assert len(results) == 1
    assert results[0]["error"] is not None
    assert results[0]["replayed_status"] is None
    assert results[0]["status_match"] is False
