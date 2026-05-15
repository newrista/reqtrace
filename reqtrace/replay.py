"""Replay recorded HTTP requests against a target host."""

import http.client
import urllib.parse
from typing import Optional

from reqtrace.models import TraceEntry, HttpRequest, HttpResponse
from reqtrace.storage import TraceStore


def _parse_url(url: str):
    """Parse a URL into (scheme, host, path+query) components."""
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return parsed.scheme, host, path


def replay_entry(
    entry: TraceEntry,
    override_host: Optional[str] = None,
    timeout: float = 10.0,
) -> HttpResponse:
    """Replay a single TraceEntry and return the new HttpResponse."""
    req: HttpRequest = entry.request
    scheme, host, path = _parse_url(req.url)

    target_host = override_host or host

    if scheme == "https":
        conn = http.client.HTTPSConnection(target_host, timeout=timeout)
    else:
        conn = http.client.HTTPConnection(target_host, timeout=timeout)

    headers = dict(req.headers)
    # Update host header to target
    headers["Host"] = target_host

    body = req.body.encode("utf-8") if req.body else None

    try:
        conn.request(req.method, path, body=body, headers=headers)
        resp = conn.getresponse()
        resp_body = resp.read().decode("utf-8", errors="replace")
        resp_headers = dict(resp.getheaders())
        return HttpResponse(
            status_code=resp.status,
            headers=resp_headers,
            body=resp_body,
        )
    finally:
        conn.close()


def replay_all(
    store: TraceStore,
    override_host: Optional[str] = None,
    timeout: float = 10.0,
) -> list[dict]:
    """Replay all entries in the store and return a list of result dicts."""
    results = []
    for entry in store.get_all():
        try:
            new_response = replay_entry(entry, override_host=override_host, timeout=timeout)
            results.append({
                "id": entry.id,
                "url": entry.request.url,
                "method": entry.request.method,
                "original_status": entry.response.status_code,
                "replayed_status": new_response.status_code,
                "status_match": entry.response.status_code == new_response.status_code,
                "error": None,
            })
        except Exception as exc:
            results.append({
                "id": entry.id,
                "url": entry.request.url,
                "method": entry.request.method,
                "original_status": entry.response.status_code,
                "replayed_status": None,
                "status_match": False,
                "error": str(exc),
            })
    return results
