"""Core data models for reqtrace."""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from datetime import datetime
from urllib.parse import urlparse, parse_qs


@dataclass
class HttpRequest:
    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[bytes] = None

    @property
    def path(self) -> str:
        return urlparse(self.url).path

    @property
    def query_params(self) -> Dict[str, list]:
        return parse_qs(urlparse(self.url).query)

    @property
    def is_json(self) -> bool:
        ct = self.headers.get("Content-Type", "")
        return "application/json" in ct

    @property
    def has_body(self) -> bool:
        return self.body is not None and len(self.body) > 0

    @property
    def host(self) -> str:
        return urlparse(self.url).netloc


@dataclass
class HttpResponse:
    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[bytes] = None

    @property
    def is_json(self) -> bool:
        ct = self.headers.get("Content-Type", "")
        return "application/json" in ct

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300


@dataclass
class TraceEntry:
    id: str
    request: HttpRequest
    response: Optional[HttpResponse] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration: Optional[float] = None  # milliseconds
