"""Diff utilities for comparing two HTTP trace entries."""

from typing import Any, Dict, List, Optional
from reqtrace.models import TraceEntry


def _dict_diff(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Return keys that differ between two dicts."""
    all_keys = set(a) | set(b)
    result = {}
    for key in all_keys:
        val_a = a.get(key)
        val_b = b.get(key)
        if val_a != val_b:
            result[key] = {"before": val_a, "after": val_b}
    return result


def diff_entries(entry_a: TraceEntry, entry_b: TraceEntry) -> Dict[str, Any]:
    """Compare two TraceEntry objects and return a structured diff."""
    result: Dict[str, Any] = {}

    # Request diffs
    req_diff: Dict[str, Any] = {}
    if entry_a.request.method != entry_b.request.method:
        req_diff["method"] = {"before": entry_a.request.method, "after": entry_b.request.method}
    if entry_a.request.path != entry_b.request.path:
        req_diff["path"] = {"before": entry_a.request.path, "after": entry_b.request.path}
    if entry_a.request.query_string != entry_b.request.query_string:
        req_diff["query_string"] = {
            "before": entry_a.request.query_string,
            "after": entry_b.request.query_string,
        }
    headers_diff = _dict_diff(
        dict(entry_a.request.headers), dict(entry_b.request.headers)
    )
    if headers_diff:
        req_diff["headers"] = headers_diff
    if entry_a.request.body != entry_b.request.body:
        req_diff["body"] = {"before": entry_a.request.body, "after": entry_b.request.body}
    if req_diff:
        result["request"] = req_diff

    # Response diffs
    resp_diff: Dict[str, Any] = {}
    if entry_a.response.status_code != entry_b.response.status_code:
        resp_diff["status_code"] = {
            "before": entry_a.response.status_code,
            "after": entry_b.response.status_code,
        }
    resp_headers_diff = _dict_diff(
        dict(entry_a.response.headers), dict(entry_b.response.headers)
    )
    if resp_headers_diff:
        resp_diff["headers"] = resp_headers_diff
    if entry_a.response.body != entry_b.response.body:
        resp_diff["body"] = {"before": entry_a.response.body, "after": entry_b.response.body}
    if resp_diff:
        result["response"] = resp_diff

    return result


def diff_summary(diff: Dict[str, Any]) -> List[str]:
    """Return a human-readable list of change descriptions from a diff result."""
    lines: List[str] = []
    for section, changes in diff.items():
        for field, delta in changes.items():
            lines.append(f"{section}.{field}: {delta['before']!r} -> {delta['after']!r}")
    return lines
