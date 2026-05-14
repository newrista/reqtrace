"""HTTP proxy module for reqtrace.

Intercepts incoming HTTP requests, forwards them to the target server,
and records both the request and response as a TraceEntry.
"""

import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
from urllib.parse import urlparse, urlunparse

import urllib.request
import urllib.error

from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.storage import TraceStore


class ProxyHandler(BaseHTTPRequestHandler):
    """HTTP request handler that proxies traffic and logs trace entries."""

    # Set by ProxyServer before use
    store: TraceStore = None
    target_base_url: str = None

    def log_message(self, format, *args):  # noqa: A002
        """Suppress default BaseHTTPRequestHandler console logging."""
        pass

    def _read_body(self) -> Optional[bytes]:
        """Read the request body if Content-Length is present."""
        length = self.headers.get("Content-Length")
        if length:
            try:
                return self.rfile.read(int(length))
            except (ValueError, OSError):
                return None
        return None

    def _build_target_url(self) -> str:
        """Construct the full target URL by combining base URL with request path."""
        base = self.target_base_url.rstrip("/")
        return base + self.path

    def _forward_request(self, method: str, body: Optional[bytes]) -> HttpResponse:
        """Forward the request to the target server and return an HttpResponse."""
        target_url = self._build_target_url()

        req_headers = {k: v for k, v in self.headers.items()}
        # Remove hop-by-hop headers
        for hop_header in ("connection", "keep-alive", "proxy-authenticate",
                           "proxy-authorization", "te", "trailers",
                           "transfer-encoding", "upgrade"):
            req_headers.pop(hop_header, None)

        upstream_req = urllib.request.Request(
            url=target_url,
            data=body,
            headers=req_headers,
            method=method,
        )

        try:
            with urllib.request.urlopen(upstream_req, timeout=10) as resp:
                resp_body = resp.read()
                resp_headers = dict(resp.headers)
                return HttpResponse(
                    status_code=resp.status,
                    headers=resp_headers,
                    body=resp_body.decode("utf-8", errors="replace") if resp_body else None,
                    content_type=resp.headers.get("Content-Type"),
                )
        except urllib.error.HTTPError as e:
            resp_body = e.read()
            return HttpResponse(
                status_code=e.code,
                headers=dict(e.headers),
                body=resp_body.decode("utf-8", errors="replace") if resp_body else None,
                content_type=e.headers.get("Content-Type"),
            )
        except urllib.error.URLError as e:
            return HttpResponse(
                status_code=502,
                headers={},
                body=f"Proxy error: {e.reason}",
                content_type="text/plain",
            )

    def _handle(self, method: str):
        """Core handler: capture request, proxy it, record trace, send response."""
        body = self._read_body()
        parsed = urlparse(self.path)

        http_request = HttpRequest(
            method=method,
            path=parsed.path,
            query_string=parsed.query or None,
            headers=dict(self.headers),
            body=body.decode("utf-8", errors="replace") if body else None,
            content_type=self.headers.get("Content-Type"),
        )

        start = time.monotonic()
        http_response = self._forward_request(method, body)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        entry = TraceEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            request=http_request,
            response=http_response,
            duration_ms=duration_ms,
        )
        self.store.add(entry)

        # Send response back to original client
        self.send_response(http_response.status_code)
        for header, value in (http_response.headers or {}).items():
            if header.lower() not in ("transfer-encoding", "connection"):
                self.send_header(header, value)
        self.end_headers()
        if http_response.body:
            self.wfile.write(http_response.body.encode("utf-8", errors="replace"))

    def do_GET(self):     self._handle("GET")
    def do_POST(self):    self._handle("POST")
    def do_PUT(self):     self._handle("PUT")
    def do_DELETE(self):  self._handle("DELETE")
    def do_PATCH(self):   self._handle("PATCH")
    def do_HEAD(self):    self._handle("HEAD")
    def do_OPTIONS(self): self._handle("OPTIONS")


class ProxyServer:
    """Wraps HTTPServer with a shared TraceStore and target URL configuration."""

    def __init__(self, host: str, port: int, target_base_url: str, store: Optional[TraceStore] = None):
        self.host = host
        self.port = port
        self.target_base_url = target_base_url
        self.store = store or TraceStore()

        # Inject dependencies into the handler class via class attributes
        handler = ProxyHandler
        handler.store = self.store
        handler.target_base_url = target_base_url

        self._server = HTTPServer((host, port), handler)

    def serve_forever(self):
        """Start the proxy server and block until interrupted."""
        print(f"[reqtrace] Proxying {self.host}:{self.port} -> {self.target_base_url}")
        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            print("\n[reqtrace] Shutting down proxy.")
        finally:
            self._server.server_close()

    def shutdown(self):
        """Programmatically stop the server (useful in tests)."""
        self._server.shutdown()
        self._server.server_close()
