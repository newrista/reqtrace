"""Data models for reqtrace HTTP traces."""

from dataclasses import dataclass, field
from typing import Dict, Optional
import datetime
import uuid


@dataclass
class HttpRequest:
    method: str
    path: str
    query_string: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    body: bytes = b""
    content_type: Optional[str] = None
    query_params: Dict[str, str] = field(default_factory=dict)

    def is_json(self) -> bool:
        return bool(self.content_type and "json" in self.content_type)

    def has_body(self) -> bool:
        return len(self.body) > 0


@dataclass
class HttpResponse:
    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)
    body: bytes = b""
    content_type: Optional[str] = None

    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def is_error(self) -> bool:
        return self.status_code >= 400

    def is_json(self) -> bool:
        return bool(self.content_type and "json" in self.content_type)


@dataclass
class TraceEntry:
    request: HttpRequest
    response: HttpResponse
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.utcnow)

    def duration_hint(self) -> str:
        """Placeholder for latency tracking in future versions."""
        return "N/A"

    def summary_line(self) -> str:
        return (
            f"[{self.timestamp.isoformat()}] "
            f"{self.request.method} {self.request.path} "
            f"-> {self.response.status_code}"
        )
