"""Deduplication utilities for trace entries."""

from typing import List, Optional
from reqtrace.models import TraceEntry


def _entry_signature(entry: TraceEntry, ignore_headers: bool = True) -> tuple:
    """Compute a signature tuple for an entry to detect duplicates."""
    req = entry.request
    method = req.method.upper()
    path = req.path
    query = tuple(sorted(req.query_params.items())) if req.query_params else ()
    body = req.body if req.body else b""
    if ignore_headers:
        return (method, path, query, body)
    headers = tuple(sorted((k.lower(), v) for k, v in req.headers.items()))
    return (method, path, query, body, headers)


def dedupe(entries: List[TraceEntry], ignore_headers: bool = True) -> List[TraceEntry]:
    """Return a list with duplicate entries removed (first occurrence kept)."""
    seen = set()
    result = []
    for entry in entries:
        sig = _entry_signature(entry, ignore_headers=ignore_headers)
        if sig not in seen:
            seen.add(sig)
            result.append(entry)
    return result


def find_duplicates(entries: List[TraceEntry], ignore_headers: bool = True) -> List[List[TraceEntry]]:
    """Group entries that are duplicates of each other.

    Returns a list of groups, each group containing 2+ duplicate entries.
    """
    from collections import defaultdict
    groups: dict = defaultdict(list)
    for entry in entries:
        sig = _entry_signature(entry, ignore_headers=ignore_headers)
        groups[sig].append(entry)
    return [group for group in groups.values() if len(group) > 1]


def count_unique(entries: List[TraceEntry], ignore_headers: bool = True) -> int:
    """Return the number of unique entries based on request signature."""
    sigs = {_entry_signature(e, ignore_headers=ignore_headers) for e in entries}
    return len(sigs)


def has_duplicates(entries: List[TraceEntry], ignore_headers: bool = True) -> bool:
    """Return True if any duplicate entries exist in the list."""
    return count_unique(entries, ignore_headers=ignore_headers) < len(entries)
