"""Core data models for HTTP request/response capture."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class HttpRequest:
    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[bytes] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def path(self) -> str:
        from urllib.parse import urlparse
        return urlparse(self.url).path

    @property
    def query_string(self) -> str:
        from urllib.parse import urlparse
        return urlparse(self.url).query

    def content_type(self) -> Optional[str]:
        return self.headers.get("content-type") or self.headers.get("Content-Type")


@dataclass
class HttpResponse:
    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[bytes] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def content_type(self) -> Optional[str]:
        return self.headers.get("content-type") or self.headers.get("Content-Type")

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300


@dataclass
class TraceEntry:
    request: HttpRequest
    response: HttpResponse
    duration_ms: float
    trace_id: str = ""

    def __post_init__(self):
        if not self.trace_id:
            import uuid
            self.trace_id = str(uuid.uuid4())

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "duration_ms": self.duration_ms,
            "request": {
                "method": self.request.method,
                "url": self.request.url,
                "headers": self.request.headers,
                "body": self.request.body.decode(errors="replace") if self.request.body else None,
                "timestamp": self.request.timestamp.isoformat(),
            },
            "response": {
                "status_code": self.response.status_code,
                "headers": self.response.headers,
                "body": self.response.body.decode(errors="replace") if self.response.body else None,
                "timestamp": self.response.timestamp.isoformat(),
            },
        }
