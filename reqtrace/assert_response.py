"""Assertion helpers for validating captured HTTP trace entries."""

from dataclasses import dataclass, field
from typing import Any, List, Optional
from reqtrace.models import TraceEntry


@dataclass
class AssertionResult:
    passed: bool
    message: str
    entry_id: str


def assert_status(entry: TraceEntry, expected: int) -> AssertionResult:
    """Assert that the response status code matches the expected value."""
    actual = entry.response.status_code
    passed = actual == expected
    msg = (
        f"Status OK: {actual}"
        if passed
        else f"Status mismatch: expected {expected}, got {actual}"
    )
    return AssertionResult(passed=passed, message=msg, entry_id=entry.id)


def assert_header_present(entry: TraceEntry, header: str) -> AssertionResult:
    """Assert that a specific response header is present (case-insensitive)."""
    headers = {k.lower(): v for k, v in entry.response.headers.items()}
    key = header.lower()
    passed = key in headers
    msg = (
        f"Header '{header}' present"
        if passed
        else f"Header '{header}' missing from response"
    )
    return AssertionResult(passed=passed, message=msg, entry_id=entry.id)


def assert_header_value(entry: TraceEntry, header: str, expected: str) -> AssertionResult:
    """Assert that a response header has the expected value (case-insensitive key)."""
    headers = {k.lower(): v for k, v in entry.response.headers.items()}
    actual = headers.get(header.lower())
    passed = actual == expected
    msg = (
        f"Header '{header}' = '{expected}'"
        if passed
        else f"Header '{header}': expected '{expected}', got '{actual}'"
    )
    return AssertionResult(passed=passed, message=msg, entry_id=entry.id)


def assert_body_contains(entry: TraceEntry, substring: str) -> AssertionResult:
    """Assert that the response body contains a given substring."""
    body = entry.response.body or ""
    passed = substring in body
    msg = (
        f"Body contains '{substring}'"
        if passed
        else f"Body does not contain '{substring}'"
    )
    return AssertionResult(passed=passed, message=msg, entry_id=entry.id)


def assert_all(
    entry: TraceEntry,
    status: Optional[int] = None,
    headers_present: Optional[List[str]] = None,
    body_contains: Optional[str] = None,
) -> List[AssertionResult]:
    """Run multiple assertions on a single entry and return all results."""
    results: List[AssertionResult] = []
    if status is not None:
        results.append(assert_status(entry, status))
    for h in headers_present or []:
        results.append(assert_header_present(entry, h))
    if body_contains is not None:
        results.append(assert_body_contains(entry, body_contains))
    return results


def all_passed(results: List[AssertionResult]) -> bool:
    """Return True if every assertion result passed."""
    return all(r.passed for r in results)
