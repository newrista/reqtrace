"""Redaction utilities for sensitive fields in HTTP traces."""

import re
from typing import Dict, List, Optional

DEFAULT_HEADER_PATTERNS = [
    re.compile(r"^authorization$", re.IGNORECASE),
    re.compile(r"^cookie$", re.IGNORECASE),
    re.compile(r"^set-cookie$", re.IGNORECASE),
    re.compile(r"^x-api-key$", re.IGNORECASE),
    re.compile(r"^x-auth-token$", re.IGNORECASE),
]

DEFAULT_QUERY_PATTERNS = [
    re.compile(r"^(api_?key|token|secret|password|passwd|pwd)$", re.IGNORECASE),
]

REDACTED = "[REDACTED]"


def redact_headers(
    headers: Dict[str, str],
    patterns: Optional[List[re.Pattern]] = None,
) -> Dict[str, str]:
    """Return a copy of headers with sensitive values replaced."""
    patterns = patterns if patterns is not None else DEFAULT_HEADER_PATTERNS
    return {
        k: REDACTED if any(p.match(k) for p in patterns) else v
        for k, v in headers.items()
    }


def redact_query_params(
    params: Dict[str, str],
    patterns: Optional[List[re.Pattern]] = None,
) -> Dict[str, str]:
    """Return a copy of query params with sensitive values replaced."""
    patterns = patterns if patterns is not None else DEFAULT_QUERY_PATTERNS
    return {
        k: REDACTED if any(p.match(k) for p in patterns) else v
        for k, v in params.items()
    }


def redact_entry(entry, header_patterns=None, query_patterns=None):
    """Return a shallow-copied entry with sensitive data redacted."""
    from reqtrace.models import HttpRequest, HttpResponse, TraceEntry

    req = entry.request
    redacted_req = HttpRequest(
        method=req.method,
        path=req.path,
        query_string=req.query_string,
        headers=redact_headers(req.headers, header_patterns),
        body=req.body,
        content_type=req.content_type,
        query_params=redact_query_params(req.query_params, query_patterns),
    )

    resp = entry.response
    redacted_resp = HttpResponse(
        status_code=resp.status_code,
        headers=redact_headers(resp.headers, header_patterns),
        body=resp.body,
        content_type=resp.content_type,
    )

    return TraceEntry(
        id=entry.id,
        timestamp=entry.timestamp,
        request=redacted_req,
        response=redacted_resp,
    )
