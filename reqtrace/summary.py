"""Summary statistics for a collection of trace entries."""

from typing import Dict, List
from collections import Counter
from reqtrace.models import TraceEntry


def summarize(entries: List[TraceEntry]) -> Dict:
    """Generate a summary dict from a list of trace entries."""
    if not entries:
        return {
            "total": 0,
            "methods": {},
            "status_codes": {},
            "error_rate": 0.0,
            "paths": {},
        }

    method_counts: Counter = Counter()
    status_counts: Counter = Counter()
    path_counts: Counter = Counter()
    error_count = 0

    for entry in entries:
        method_counts[entry.request.method.upper()] += 1
        status_counts[entry.response.status_code] += 1
        path_counts[entry.request.path] += 1
        if entry.response.status_code >= 400:
            error_count += 1

    return {
        "total": len(entries),
        "methods": dict(method_counts),
        "status_codes": {str(k): v for k, v in status_counts.items()},
        "error_rate": round(error_count / len(entries), 4),
        "paths": dict(path_counts),
    }


def top_paths(entries: List[TraceEntry], n: int = 5) -> List[Dict]:
    """Return the top N most frequently requested paths."""
    counts: Counter = Counter(e.request.path for e in entries)
    return [
        {"path": path, "count": count}
        for path, count in counts.most_common(n)
    ]
