"""Filtering and querying utilities for trace entries."""

from typing import List, Optional
from reqtrace.models import TraceEntry


def filter_by_method(entries: List[TraceEntry], method: str) -> List[TraceEntry]:
    """Return entries matching the given HTTP method (case-insensitive)."""
    method_upper = method.upper()
    return [e for e in entries if e.request.method.upper() == method_upper]


def filter_by_path(entries: List[TraceEntry], path_prefix: str) -> List[TraceEntry]:
    """Return entries whose request path starts with the given prefix."""
    return [e for e in entries if e.request.path.startswith(path_prefix)]


def filter_by_status(entries: List[TraceEntry], status_code: int) -> List[TraceEntry]:
    """Return entries whose response status code matches."""
    return [e for e in entries if e.response.status_code == status_code]


def filter_by_status_range(
    entries: List[TraceEntry], min_status: int, max_status: int
) -> List[TraceEntry]:
    """Return entries whose response status code falls within [min_status, max_status]."""
    return [
        e for e in entries
        if min_status <= e.response.status_code <= max_status
    ]


def filter_by_content_type(
    entries: List[TraceEntry], content_type: str
) -> List[TraceEntry]:
    """Return entries whose request Content-Type contains the given string."""
    return [
        e for e in entries
        if e.request.content_type and content_type.lower() in e.request.content_type.lower()
    ]


def search_entries(
    entries: List[TraceEntry],
    method: Optional[str] = None,
    path_prefix: Optional[str] = None,
    status_code: Optional[int] = None,
    content_type: Optional[str] = None,
) -> List[TraceEntry]:
    """Apply multiple optional filters to a list of trace entries."""
    result = entries
    if method is not None:
        result = filter_by_method(result, method)
    if path_prefix is not None:
        result = filter_by_path(result, path_prefix)
    if status_code is not None:
        result = filter_by_status(result, status_code)
    if content_type is not None:
        result = filter_by_content_type(result, content_type)
    return result
