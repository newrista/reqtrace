"""Tag and label trace entries for grouping and filtering."""

from typing import List, Optional
from reqtrace.models import TraceEntry


def add_tag(entry: TraceEntry, tag: str) -> TraceEntry:
    """Return a new TraceEntry with the given tag added to metadata."""
    tags = list(entry.tags) if entry.tags else []
    if tag not in tags:
        tags.append(tag)
    return entry._replace(tags=tags)


def remove_tag(entry: TraceEntry, tag: str) -> TraceEntry:
    """Return a new TraceEntry with the given tag removed."""
    tags = [t for t in (entry.tags or []) if t != tag]
    return entry._replace(tags=tags)


def filter_by_tag(entries: List[TraceEntry], tag: str) -> List[TraceEntry]:
    """Return entries that have the specified tag."""
    return [e for e in entries if tag in (e.tags or [])]


def filter_by_any_tag(entries: List[TraceEntry], tags: List[str]) -> List[TraceEntry]:
    """Return entries that have at least one of the specified tags."""
    tag_set = set(tags)
    return [e for e in entries if tag_set.intersection(e.tags or [])]


def filter_by_all_tags(entries: List[TraceEntry], tags: List[str]) -> List[TraceEntry]:
    """Return entries that have all of the specified tags."""
    tag_set = set(tags)
    return [e for e in entries if tag_set.issubset(e.tags or [])]


def list_tags(entries: List[TraceEntry]) -> List[str]:
    """Return a sorted list of all unique tags across entries."""
    all_tags: set = set()
    for e in entries:
        all_tags.update(e.tags or [])
    return sorted(all_tags)


def auto_tag(entry: TraceEntry) -> TraceEntry:
    """Automatically apply tags based on request/response properties."""
    tags = list(entry.tags or [])

    method = entry.request.method.upper()
    if method not in tags:
        tags.append(method)

    status = entry.response.status_code
    if 200 <= status < 300 and "success" not in tags:
        tags.append("success")
    elif 400 <= status < 500 and "client-error" not in tags:
        tags.append("client-error")
    elif 500 <= status < 600 and "server-error" not in tags:
        tags.append("server-error")

    return entry._replace(tags=tags)
