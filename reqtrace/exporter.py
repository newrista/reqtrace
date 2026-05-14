"""Export trace entries to various output formats (JSON, HAR)."""

import json
from datetime import datetime, timezone
from typing import List

from reqtrace.models import TraceEntry


def export_json(entries: List[TraceEntry], indent: int = 2) -> str:
    """Serialize a list of trace entries to a JSON string."""
    records = []
    for entry in entries:
        records.append({
            "id": entry.id,
            "timestamp": entry.timestamp.isoformat(),
            "request": {
                "method": entry.request.method,
                "url": entry.request.url,
                "path": entry.request.path,
                "query_string": entry.request.query_string,
                "headers": dict(entry.request.headers),
                "body": entry.request.body,
                "content_type": entry.request.content_type,
            },
            "response": {
                "status_code": entry.response.status_code,
                "headers": dict(entry.response.headers),
                "body": entry.response.body,
                "content_type": entry.response.content_type,
                "elapsed_ms": entry.response.elapsed_ms,
            },
        })
    return json.dumps(records, indent=indent, default=str)


def export_har(entries: List[TraceEntry]) -> str:
    """Serialize a list of trace entries to a HAR (HTTP Archive) JSON string."""
    har_entries = []
    for entry in entries:
        req = entry.request
        resp = entry.response

        query_params = [
            {"name": k, "value": v}
            for k, v in (entry.request.query_params or {}).items()
        ]

        request_headers = [
            {"name": k, "value": v} for k, v in req.headers.items()
        ]
        response_headers = [
            {"name": k, "value": v} for k, v in resp.headers.items()
        ]

        har_entries.append({
            "startedDateTime": entry.timestamp.astimezone(timezone.utc).isoformat(),
            "time": resp.elapsed_ms if resp.elapsed_ms is not None else 0,
            "request": {
                "method": req.method,
                "url": req.url,
                "httpVersion": "HTTP/1.1",
                "headers": request_headers,
                "queryString": query_params,
                "postData": {
                    "mimeType": req.content_type or "",
                    "text": req.body or "",
                } if req.body else None,
                "headersSize": -1,
                "bodySize": len(req.body.encode()) if req.body else 0,
            },
            "response": {
                "status": resp.status_code,
                "statusText": "",
                "httpVersion": "HTTP/1.1",
                "headers": response_headers,
                "content": {
                    "size": len(resp.body.encode()) if resp.body else 0,
                    "mimeType": resp.content_type or "application/octet-stream",
                    "text": resp.body or "",
                },
                "redirectURL": "",
                "headersSize": -1,
                "bodySize": len(resp.body.encode()) if resp.body else 0,
            },
            "cache": {},
            "timings": {
                "send": 0,
                "wait": resp.elapsed_ms if resp.elapsed_ms is not None else 0,
                "receive": 0,
            },
        })

    har = {
        "log": {
            "version": "1.2",
            "creator": {"name": "reqtrace", "version": "0.1.0"},
            "entries": har_entries,
        }
    }
    return json.dumps(har, indent=2, default=str)
