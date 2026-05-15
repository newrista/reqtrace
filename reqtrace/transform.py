"""Transform trace entries: modify headers, body, or metadata for replay or export."""

from typing import Callable, Dict, List, Optional
from reqtrace.models import TraceEntry, HttpRequest, HttpResponse


def set_request_header(entry: TraceEntry, key: str, value: str) -> TraceEntry:
    """Return a new entry with the given request header set (or overwritten)."""
    new_headers = dict(entry.request.headers)
    new_headers[key] = value
    new_req = HttpRequest(
        method=entry.request.method,
        url=entry.request.url,
        headers=new_headers,
        body=entry.request.body,
    )
    return TraceEntry(
        id=entry.id,
        request=new_req,
        response=entry.response,
        timestamp=entry.timestamp,
        metadata=entry.metadata,
        tags=list(entry.tags),
    )


def remove_request_header(entry: TraceEntry, key: str) -> TraceEntry:
    """Return a new entry with the given request header removed (case-insensitive)."""
    new_headers = {k: v for k, v in entry.request.headers.items() if k.lower() != key.lower()}
    new_req = HttpRequest(
        method=entry.request.method,
        url=entry.request.url,
        headers=new_headers,
        body=entry.request.body,
    )
    return TraceEntry(
        id=entry.id,
        request=new_req,
        response=entry.response,
        timestamp=entry.timestamp,
        metadata=entry.metadata,
        tags=list(entry.tags),
    )


def set_response_header(entry: TraceEntry, key: str, value: str) -> TraceEntry:
    """Return a new entry with the given response header set (or overwritten)."""
    if entry.response is None:
        return entry
    new_headers = dict(entry.response.headers)
    new_headers[key] = value
    new_resp = HttpResponse(
        status_code=entry.response.status_code,
        headers=new_headers,
        body=entry.response.body,
    )
    return TraceEntry(
        id=entry.id,
        request=entry.request,
        response=new_resp,
        timestamp=entry.timestamp,
        metadata=entry.metadata,
        tags=list(entry.tags),
    )


def replace_request_body(entry: TraceEntry, new_body: Optional[bytes]) -> TraceEntry:
    """Return a new entry with the request body replaced."""
    new_req = HttpRequest(
        method=entry.request.method,
        url=entry.request.url,
        headers=entry.request.headers,
        body=new_body,
    )
    return TraceEntry(
        id=entry.id,
        request=new_req,
        response=entry.response,
        timestamp=entry.timestamp,
        metadata=entry.metadata,
        tags=list(entry.tags),
    )


def apply_transforms(entry: TraceEntry, transforms: List[Callable[[TraceEntry], TraceEntry]]) -> TraceEntry:
    """Apply a sequence of transform functions to an entry, returning the final result."""
    for fn in transforms:
        entry = fn(entry)
    return entry
