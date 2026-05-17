"""Tests for reqtrace/lint.py"""

import pytest
from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.lint import lint_entry, lint_all, lint_summary, LintIssue


def _make_entry(
    url="http://example.com/api",
    method="GET",
    req_headers=None,
    req_body=None,
    req_content_type=None,
    status=200,
    resp_body=None,
    entry_id="test-id",
) -> TraceEntry:
    request = HttpRequest(
        method=method,
        url=url,
        headers=req_headers or {},
        body=req_body,
        content_type=req_content_type,
    )
    response = HttpResponse(
        status_code=status,
        headers={},
        body=resp_body,
    )
    return TraceEntry(id=entry_id, request=request, response=response)


def test_lint_clean_entry_has_no_issues():
    entry = _make_entry()
    result = lint_entry(entry)
    assert result.issues == []
    assert not result.has_errors
    assert not result.has_warnings


def test_lint_body_without_content_type_warns():
    entry = _make_entry(req_body=b'{"x": 1}', req_content_type=None)
    result = lint_entry(entry)
    codes = [i.code for i in result.issues]
    assert "W001" in codes


def test_lint_body_with_content_type_no_warn():
    entry = _make_entry(req_body=b'{"x": 1}', req_content_type="application/json")
    result = lint_entry(entry)
    codes = [i.code for i in result.issues]
    assert "W001" not in codes


def test_lint_large_response_body_info():
    big_body = b"x" * (1_048_576 + 1)
    entry = _make_entry(resp_body=big_body)
    result = lint_entry(entry)
    codes = [i.code for i in result.issues]
    assert "I001" in codes
    assert result.issues[0].severity == "info"


def test_lint_small_response_body_no_info():
    entry = _make_entry(resp_body=b"small")
    result = lint_entry(entry)
    codes = [i.code for i in result.issues]
    assert "I001" not in codes


def test_lint_error_status_no_body_warns():
    entry = _make_entry(status=404, resp_body=None)
    result = lint_entry(entry)
    codes = [i.code for i in result.issues]
    assert "W002" in codes


def test_lint_error_status_with_body_no_warn():
    entry = _make_entry(status=404, resp_body=b"Not Found")
    result = lint_entry(entry)
    codes = [i.code for i in result.issues]
    assert "W002" not in codes


def test_lint_auth_over_http_is_error():
    entry = _make_entry(
        url="http://example.com/secure",
        req_headers={"Authorization": "Bearer token123"},
    )
    result = lint_entry(entry)
    codes = [i.code for i in result.issues]
    assert "E001" in codes
    assert result.has_errors


def test_lint_auth_over_https_no_error():
    entry = _make_entry(
        url="https://example.com/secure",
        req_headers={"Authorization": "Bearer token123"},
    )
    result = lint_entry(entry)
    codes = [i.code for i in result.issues]
    assert "E001" not in codes


def test_lint_all_returns_one_result_per_entry():
    entries = [_make_entry(entry_id=str(i)) for i in range(5)]
    results = lint_all(entries)
    assert len(results) == 5


def test_lint_summary_counts_correctly():
    e1 = _make_entry(url="http://x.com", req_headers={"Authorization": "Bearer t"}, entry_id="e1")
    e2 = _make_entry(req_body=b"data", req_content_type=None, entry_id="e2")
    e3 = _make_entry(entry_id="e3")
    results = lint_all([e1, e2, e3])
    summary = lint_summary(results)
    assert summary["entries_checked"] == 3
    assert summary["errors"] >= 1
    assert summary["warnings"] >= 1
    assert summary["entries_with_issues"] >= 2
