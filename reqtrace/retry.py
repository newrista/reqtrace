"""Retry analysis: detect retried requests and summarize retry patterns."""

from collections import defaultdict
from typing import Dict, List, Tuple
from reqtrace.models import TraceEntry


def _request_key(entry: TraceEntry) -> Tuple[str, str, str]:
    """Return a tuple identifying a logical request (method, host, path)."""
    req = entry.request
    host = req.headers.get("host", req.headers.get("Host", ""))
    return (req.method.upper(), host, req.path)


def group_by_request(entries: List[TraceEntry]) -> Dict[Tuple, List[TraceEntry]]:
    """Group entries by (method, host, path) to find repeated requests."""
    groups: Dict[Tuple, List[TraceEntry]] = defaultdict(list)
    for entry in entries:
        key = _request_key(entry)
        groups[key].append(entry)
    return dict(groups)


def find_retries(entries: List[TraceEntry], min_count: int = 2) -> Dict[Tuple, List[TraceEntry]]:
    """Return groups of entries that appear to be retried (same method+host+path, count >= min_count)."""
    groups = group_by_request(entries)
    return {key: group for key, group in groups.items() if len(group) >= min_count}


def has_retries(entries: List[TraceEntry]) -> bool:
    """Return True if any request appears more than once."""
    return bool(find_retries(entries))


def retry_summary(entries: List[TraceEntry]) -> List[Dict]:
    """Return a summary list of retried request groups with counts and status codes."""
    retries = find_retries(entries)
    summary = []
    for (method, host, path), group in sorted(retries.items(), key=lambda x: -len(x[1])):
        statuses = [e.response.status_code for e in group if e.response is not None]
        summary.append({
            "method": method,
            "host": host,
            "path": path,
            "count": len(group),
            "status_codes": statuses,
            "has_error": any(s >= 400 for s in statuses),
        })
    return summary


def successful_after_retry(entries: List[TraceEntry]) -> List[Dict]:
    """Return retry groups where at least one attempt failed and a later one succeeded."""
    retries = find_retries(entries)
    result = []
    for (method, host, path), group in retries.items():
        sorted_group = sorted(group, key=lambda e: e.timestamp)
        statuses = [e.response.status_code if e.response else None for e in sorted_group]
        valid = [s for s in statuses if s is not None]
        if valid and any(s >= 400 for s in valid[:-1]) and valid[-1] < 400:
            result.append({
                "method": method,
                "host": host,
                "path": path,
                "attempts": len(group),
                "final_status": valid[-1],
            })
    return result
