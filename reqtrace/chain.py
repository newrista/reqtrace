"""Chain analysis: detect sequences of related HTTP requests by session, path prefix, or timing proximity."""

from typing import List, Dict, Optional
from datetime import timedelta
from reqtrace.models import TraceEntry


def group_by_session(
    entries: List[TraceEntry],
    session_header: str = "X-Session-Id",
) -> Dict[str, List[TraceEntry]]:
    """Group entries by a session identifier found in request headers."""
    groups: Dict[str, List[TraceEntry]] = {}
    for entry in entries:
        headers = entry.request.headers or {}
        # case-insensitive lookup
        session_id = next(
            (v for k, v in headers.items() if k.lower() == session_header.lower()),
            None,
        )
        key = session_id if session_id is not None else "__unknown__"
        groups.setdefault(key, []).append(entry)
    return groups


def group_by_path_prefix(
    entries: List[TraceEntry],
    depth: int = 1,
) -> Dict[str, List[TraceEntry]]:
    """Group entries by the first *depth* path segments."""
    groups: Dict[str, List[TraceEntry]] = {}
    for entry in entries:
        parts = [p for p in entry.request.path.split("/") if p]
        prefix = "/" + "/".join(parts[:depth]) if parts else "/"
        groups.setdefault(prefix, []).append(entry)
    return groups


def find_chains(
    entries: List[TraceEntry],
    gap_seconds: float = 2.0,
) -> List[List[TraceEntry]]:
    """Split a sorted list of entries into chains where consecutive requests
    are within *gap_seconds* of each other."""
    if not entries:
        return []

    sorted_entries = sorted(entries, key=lambda e: e.timestamp)
    chains: List[List[TraceEntry]] = []
    current: List[TraceEntry] = [sorted_entries[0]]

    for prev, curr in zip(sorted_entries, sorted_entries[1:]):
        delta = (curr.timestamp - prev.timestamp).total_seconds()
        if delta <= gap_seconds:
            current.append(curr)
        else:
            chains.append(current)
            current = [curr]

    chains.append(current)
    return chains


def chain_summary(chains: List[List[TraceEntry]]) -> List[Dict]:
    """Return a summary dict for each chain."""
    summaries = []
    for i, chain in enumerate(chains):
        methods = [e.request.method for e in chain]
        paths = [e.request.path for e in chain]
        statuses = [e.response.status_code for e in chain]
        duration = (
            (chain[-1].timestamp - chain[0].timestamp).total_seconds()
            if len(chain) > 1
            else 0.0
        )
        summaries.append(
            {
                "chain_index": i,
                "length": len(chain),
                "duration_seconds": round(duration, 4),
                "methods": methods,
                "paths": paths,
                "statuses": statuses,
            }
        )
    return summaries
