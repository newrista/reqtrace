"""Tests for reqtrace.validate."""

from __future__ import annotations

import pytest

from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.validate import (
    ValidationResult,
    validate_all,
    validate_entry,
)


OPENAPI = {
    "openapi": "3.0.0",
    "info": {"title": "Test", "version": "1.0"},
    "paths": {
        "/users": {
            "get": {
                "responses": {
                    "200": {"description": "ok"},
                    "404": {"description": "not found"},
                }
            },
            "post": {
                "requestBody": {
                    "content": {"application/json": {}}
                },
                "responses": {"201": {"description": "created"}},
            },
        }
    },
}


def _make_entry(
    path: str = "/users",
    method: str = "GET",
    status: int = 200,
    content_type: str | None = None,
) -> TraceEntry:
    headers = {}
    if content_type:
        headers["content-type"] = content_type
    req = HttpRequest(method=method, path=path, headers=headers, body=None)
    resp = HttpResponse(status_code=status, headers={}, body=None)
    return TraceEntry(request=req, response=resp)


def test_valid_get_request():
    entry = _make_entry(path="/users", method="GET", status=200)
    result = validate_entry(entry, OPENAPI)
    assert result.is_valid
    assert result.errors == []


def test_invalid_status_code():
    entry = _make_entry(path="/users", method="GET", status=500)
    result = validate_entry(entry, OPENAPI)
    assert not result.is_valid
    assert any("500" in e for e in result.errors)


def test_path_not_in_schema():
    entry = _make_entry(path="/unknown", method="GET", status=200)
    result = validate_entry(entry, OPENAPI)
    assert not result.is_valid
    assert any("not found in schema" in e for e in result.errors)


def test_method_not_in_schema():
    entry = _make_entry(path="/users", method="DELETE", status=200)
    result = validate_entry(entry, OPENAPI)
    assert not result.is_valid
    assert any("not found in schema" in e for e in result.errors)


def test_valid_post_with_correct_content_type():
    entry = _make_entry(
        path="/users", method="POST", status=201,
        content_type="application/json"
    )
    result = validate_entry(entry, OPENAPI)
    assert result.is_valid


def test_invalid_content_type_for_post():
    entry = _make_entry(
        path="/users", method="POST", status=201,
        content_type="text/plain"
    )
    result = validate_entry(entry, OPENAPI)
    assert not result.is_valid
    assert any("text/plain" in e for e in result.errors)


def test_content_type_with_charset_stripped():
    entry = _make_entry(
        path="/users", method="POST", status=201,
        content_type="application/json; charset=utf-8"
    )
    result = validate_entry(entry, OPENAPI)
    assert result.is_valid


def test_validate_all_returns_one_result_per_entry():
    entries = [
        _make_entry(status=200),
        _make_entry(status=404),
        _make_entry(status=500),
    ]
    results = validate_all(entries, OPENAPI)
    assert len(results) == 3
    assert results[0].is_valid
    assert results[1].is_valid
    assert not results[2].is_valid


def test_validation_result_metadata():
    entry = _make_entry(path="/users", method="GET", status=200)
    result = validate_entry(entry, OPENAPI)
    assert result.path == "/users"
    assert result.method == "GET"
    assert result.entry_id == entry.id
