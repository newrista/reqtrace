"""High-level comparison helpers for trace stores and entry lists."""

from typing import Dict, List, Optional, Tuple
from reqtrace.models import TraceEntry
from reqtrace.diff import diff_entries, diff_summary


def compare_by_index(
    entries_a: List[TraceEntry],
    entries_b: List[TraceEntry],
) -> List[Dict]:
    """Pair entries by position and return a list of diff reports.

    Only the first min(len(entries_a), len(entries_b)) entries are compared.
    Unmatched trailing entries in either list are silently ignored.
    """
    results = []
    pairs = zip(entries_a, entries_b)
    for i, (a, b) in enumerate(pairs):
        delta = diff_entries(a, b)
        results.append(
            {
                "index": i,
                "id_a": a.id,
                "id_b": b.id,
                "changed": bool(delta),
                "diff": delta,
                "summary": diff_summary(delta),
            }
        )
    return results


def compare_by_path_method(
    entries_a: List[TraceEntry],
    entries_b: List[TraceEntry],
) -> List[Dict]:
    """Match entries by (method, path) and diff matched pairs.

    Entries in *entries_a* that have no counterpart in *entries_b* are
    included in the result with ``changed=None`` and a descriptive summary.
    Entries present only in *entries_b* are not reported.
    """
    index_b: Dict[Tuple[str, str], TraceEntry] = {
        (e.request.method, e.request.path): e for e in entries_b
    }
    results = []
    for a in entries_a:
        key = (a.request.method, a.request.path)
        b = index_b.get(key)
        if b is None:
            results.append(
                {
                    "key": f"{key[0]} {key[1]}",
                    "id_a": a.id,
                    "id_b": None,
                    "changed": None,
                    "diff": None,
                    "summary": ["no matching entry in second set"],
                }
            )
        else:
            delta = diff_entries(a, b)
            results.append(
                {
                    "key": f"{key[0]} {key[1]}",
                    "id_a": a.id,
                    "id_b": b.id,
                    "changed": bool(delta),
                    "diff": delta,
                    "summary": diff_summary(delta),
                }
            )
    return results


def changed_only(comparison: List[Dict]) -> List[Dict]:
    """Filter a comparison result to only entries with changes."""
    return [c for c in comparison if c.get("changed")]


def unmatched_only(comparison: List[Dict]) -> List[Dict]:
    """Return entries from a comparison result that had no match in the second set.

    These are entries where ``changed`` is ``None``, indicating that no
    counterpart was found during matching (e.g. from ``compare_by_path_method``).
    """
    return [c for c in comparison if c.get("changed") is None]
