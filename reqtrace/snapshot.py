"""Snapshot support: save and load trace stores to/from JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.storage import TraceStore


def _entry_to_dict(entry: TraceEntry) -> dict:
    return {
        "id": entry.id,
        "timestamp": entry.timestamp,
        "tags": list(entry.tags),
        "metadata": dict(entry.metadata) if entry.metadata else {},
        "request": {
            "method": entry.request.method,
            "url": entry.request.url,
            "headers": dict(entry.request.headers),
            "body": entry.request.body,
        },
        "response": {
            "status_code": entry.response.status_code,
            "headers": dict(entry.response.headers),
            "body": entry.response.body,
        },
    }


def _entry_from_dict(data: dict) -> TraceEntry:
    req = HttpRequest(
        method=data["request"]["method"],
        url=data["request"]["url"],
        headers=data["request"]["headers"],
        body=data["request"].get("body"),
    )
    resp = HttpResponse(
        status_code=data["response"]["status_code"],
        headers=data["response"]["headers"],
        body=data["response"].get("body"),
    )
    entry = TraceEntry(request=req, response=resp)
    entry.id = data["id"]
    entry.timestamp = data["timestamp"]
    entry.tags = set(data.get("tags", []))
    entry.metadata = data.get("metadata", {})
    return entry


def save_snapshot(store: TraceStore, path: str | Path) -> None:
    """Serialize all entries in *store* to a JSON file at *path*."""
    entries = [_entry_to_dict(e) for e in store.get_all()]
    Path(path).write_text(json.dumps(entries, indent=2), encoding="utf-8")


def load_snapshot(path: str | Path) -> TraceStore:
    """Deserialize a snapshot file and return a populated TraceStore."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    store = TraceStore()
    for item in raw:
        entry = _entry_from_dict(item)
        store._entries[entry.id] = entry
    return store


def merge_snapshots(paths: List[str | Path]) -> TraceStore:
    """Load multiple snapshot files and merge them into one TraceStore.

    Entries with duplicate IDs are deduplicated (first occurrence wins).
    """
    merged = TraceStore()
    for p in paths:
        partial = load_snapshot(p)
        for entry in partial.get_all():
            if entry.id not in merged._entries:
                merged._entries[entry.id] = entry
    return merged
