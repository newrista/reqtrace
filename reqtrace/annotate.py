"""Annotation support for trace entries — attach arbitrary key/value metadata."""

from typing import Any
from reqtrace.models import TraceEntry


def annotate(entry: TraceEntry, key: str, value: Any) -> TraceEntry:
    """Add or update a single annotation on a trace entry.

    Annotations are stored in entry.metadata under the 'annotations' key.
    """
    if entry.metadata is None:
        entry.metadata = {}
    if "annotations" not in entry.metadata:
        entry.metadata["annotations"] = {}
    entry.metadata["annotations"][key] = value
    return entry


def get_annotation(entry: TraceEntry, key: str, default: Any = None) -> Any:
    """Retrieve a single annotation value by key."""
    try:
        return entry.metadata["annotations"][key]
    except (TypeError, KeyError):
        return default


def get_all_annotations(entry: TraceEntry) -> dict:
    """Return all annotations for an entry, or an empty dict if none exist."""
    try:
        return dict(entry.metadata["annotations"])
    except (TypeError, KeyError):
        return {}


def remove_annotation(entry: TraceEntry, key: str) -> TraceEntry:
    """Remove an annotation by key. No-op if key does not exist."""
    try:
        entry.metadata["annotations"].pop(key, None)
    except (TypeError, KeyError):
        pass
    return entry


def filter_by_annotation(entries: list, key: str, value: Any = None) -> list:
    """Return entries that have the given annotation key.

    If *value* is provided, also match the annotation value exactly.
    """
    result = []
    for entry in entries:
        annotations = get_all_annotations(entry)
        if key in annotations:
            if value is None or annotations[key] == value:
                result.append(entry)
    return result


def clear_annotations(entry: TraceEntry) -> TraceEntry:
    """Remove all annotations from an entry."""
    try:
        entry.metadata.pop("annotations", None)
    except (TypeError, AttributeError):
        pass
    return entry
