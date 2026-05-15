"""Core data models for reqtrace."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class HttpRequest:
    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes | None = None
    query_string: str = ""
    http_version: str = "HTTP/1.1"

    def is_json(self) -> bool:
        ct = self.headers.get("content-type", "")
        return "application/json" in ct

    def has_body(self) -> bool:
        return self.body is not None and len(self.body) > 0


@dataclass
class HttpResponse:
    status_code: int
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes | None = None

    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def is_json(self) -> bool:
        ct = self.headers.get("content-type", "")
        return "application/json" in ct

    def has_body(self) -> bool:
        return self.body is not None and len(self.body) > 0


@dataclass
class TraceEntry:
    request: HttpRequest
    response: HttpResponse | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    duration_ms: float | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        status = self.response.status_code if self.response else "?"
        return (
            f"[{self.timestamp.isoformat()}] "
            f"{self.request.method} {self.request.path} -> {status}"
        )
