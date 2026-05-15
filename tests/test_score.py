"""Tests for reqtrace.score."""

from __future__ import annotations

import pytest

from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.score import (
    SCORE_HAS_AUTH_HEADER,
    SCORE_HAS_ERROR_STATUS,
    SCORE_HAS_QUERY_PARAMS,
    SCORE_HAS_REQUEST_BODY,
    SCORE_HAS_RESPONSE_BODY,
    SCORE_SLOW_BONUS,
    score_entry,
    score_all,
    top_scored,
)


def _make_entry(
    method="GET",
    path="/api/test",
    status=200,
    req_body=None,
    resp_body=None,
    headers=None,
    query_params=None,
    duration_ms=None,
    tags=None,
) -> TraceEntry:
    request = HttpRequest(
        method=method,
        url=f"http://example.com{path}",
        headers=headers or {},
        body=req_body,
        query_params=query_params or {},
    )
    response = HttpResponse(
        status_code=status,
        headers={},
        body=resp_body,
    )
    metadata = {}
    if tags:
        metadata["tags"] = tags
    return TraceEntry(
        request=request,
        response=response,
        duration_ms=duration_ms,
        metadata=metadata or None,
    )


def test_score_clean_entry_is_zero():
    entry = _make_entry()
    assert score_entry(entry) == 0


def test_score_error_status():
    entry = _make_entry(status=500)
    assert score_entry(entry) >= SCORE_HAS_ERROR_STATUS


def test_score_request_body():
    entry = _make_entry(req_body=b'{"key": "value"}')
    assert score_entry(entry) >= SCORE_HAS_REQUEST_BODY


def test_score_response_body():
    entry = _make_entry(resp_body=b'ok')
    assert score_entry(entry) >= SCORE_HAS_RESPONSE_BODY


def test_score_slow_response():
    entry = _make_entry(duration_ms=1000)
    assert score_entry(entry) >= SCORE_SLOW_BONUS


def test_score_fast_response_no_bonus():
    entry = _make_entry(duration_ms=100)
    assert score_entry(entry) == 0


def test_score_auth_header():
    entry = _make_entry(headers={"Authorization": "Bearer token123"})
    assert score_entry(entry) >= SCORE_HAS_AUTH_HEADER


def test_score_query_params():
    entry = _make_entry(query_params={"page": "1"})
    assert score_entry(entry) >= SCORE_HAS_QUERY_PARAMS


def test_score_tags_add_points():
    entry = _make_entry(tags=["important", "retry"])
    assert score_entry(entry) > 0


def test_score_tags_capped():
    many_tags = [f"tag{i}" for i in range(50)]
    entry = _make_entry(tags=many_tags)
    from reqtrace.score import SCORE_TAG_CAP
    # tag contribution must not exceed cap
    base = score_entry(_make_entry())
    tag_contribution = score_entry(entry) - base
    assert tag_contribution <= SCORE_TAG_CAP


def test_score_all_sorted_descending():
    entries = [
        _make_entry(status=200),
        _make_entry(status=500),
        _make_entry(status=404, req_body=b'x'),
    ]
    scored = score_all(entries)
    scores = [s for s, _ in scored]
    assert scores == sorted(scores, reverse=True)


def test_top_scored_returns_correct_count():
    entries = [_make_entry(status=200 + i) for i in range(20)]
    top = top_scored(entries, n=5)
    assert len(top) == 5


def test_top_scored_empty():
    assert top_scored([]) == []
