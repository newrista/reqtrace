"""Group and bucket trace entries by various dimensions."""

from collections import defaultdict
from typing import Dict, List, Callable, Any

from reqtrace.models import TraceEntry


def group_by_method(entries: List[TraceEntry]) -> Dict[str, List[TraceEntry]]:
    """Group entries by HTTP method."""
    groups: Dict[str, List[TraceEntry]] = defaultdict(list)
    for entry in entries:
        groups[entry.request.method.upper()].append(entry)
    return dict(groups)


def group_by_path(entries: List[TraceEntry]) -> Dict[str, List[TraceEntry]]:
    """Group entries by request path (without query string)."""
    groups: Dict[str, List[TraceEntry]] = defaultdict(list)
    for entry in entries:
        groups[entry.request.path].append(entry)
    return dict(groups)


def group_by_status(entries: List[TraceEntry]) -> Dict[int, List[TraceEntry]]:
    """Group entries by HTTP response status code."""
    groups: Dict[int, List[TraceEntry]] = defaultdict(list)
    for entry in entries:
        if entry.response is not None:
            groups[entry.response.status_code].append(entry)
    return dict(groups)


def group_by_status_class(entries: List[TraceEntry]) -> Dict[str, List[TraceEntry]]:
    """Group entries by status class (2xx, 3xx, 4xx, 5xx, etc.)."""
    groups: Dict[str, List[TraceEntry]] = defaultdict(list)
    for entry in entries:
        if entry.response is not None:
            cls = f"{entry.response.status_code // 100}xx"
            groups[cls].append(entry)
    return dict(groups)


def group_by_host(entries: List[TraceEntry]) -> Dict[str, List[TraceEntry]]:
    """Group entries by target host derived from request headers."""
    groups: Dict[str, List[TraceEntry]] = defaultdict(list)
    for entry in entries:
        host = entry.request.headers.get("host") or entry.request.headers.get("Host") or "unknown"
        groups[host].append(entry)
    return dict(groups)


def group_by(entries: List[TraceEntry], key_fn: Callable[[TraceEntry], Any]) -> Dict[Any, List[TraceEntry]]:
    """Group entries by an arbitrary key function."""
    groups: Dict[Any, List[TraceEntry]] = defaultdict(list)
    for entry in entries:
        groups[key_fn(entry)].append(entry)
    return dict(groups)
