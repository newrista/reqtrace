"""Timeline utilities for ordering and analyzing trace entries by time."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from reqtrace.models import TraceEntry


def sort_by_time(entries: List[TraceEntry], reverse: bool = False) -> List[TraceEntry]:
    """Sort entries by their timestamp ascending (or descending if reverse=True)."""
    return sorted(entries, key=lambda e: e.timestamp, reverse=reverse)


def entries_in_range(
    entries: List[TraceEntry],
    start: datetime,
    end: datetime,
) -> List[TraceEntry]:
    """Return entries whose timestamp falls within [start, end]."""
    return [e for e in entries if start <= e.timestamp <= end]


def duration_ms(entry: TraceEntry) -> Optional[float]:
    """Return request duration in milliseconds if both timestamps are present."""
    if entry.response and hasattr(entry, 'duration') and entry.duration is not None:
        return entry.duration
    return None


def slowest(entries: List[TraceEntry], n: int = 5) -> List[TraceEntry]:
    """Return the n slowest entries by duration (entries without duration are excluded)."""
    with_duration = [e for e in entries if duration_ms(e) is not None]
    return sorted(with_duration, key=lambda e: e.duration, reverse=True)[:n]


def timeline_summary(entries: List[TraceEntry]) -> Dict[str, Any]:
    """Return a summary dict describing the timeline of entries."""
    if not entries:
        return {"count": 0, "earliest": None, "latest": None, "span_seconds": None}

    sorted_entries = sort_by_time(entries)
    earliest = sorted_entries[0].timestamp
    latest = sorted_entries[-1].timestamp
    span = (latest - earliest).total_seconds()

    durations = [e.duration for e in entries if getattr(e, 'duration', None) is not None]
    avg_duration = sum(durations) / len(durations) if durations else None

    return {
        "count": len(entries),
        "earliest": earliest.isoformat(),
        "latest": latest.isoformat(),
        "span_seconds": span,
        "avg_duration_ms": avg_duration,
    }
