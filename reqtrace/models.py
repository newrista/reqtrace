"""Core data models for reqtrace."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs


@dataclass
class HttpRequest:
    method: str
    url: str
    headers: Dict[str, str]
    body: Optional[bytes]

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


@dataclass
class HttpResponse:
    status_code: int
    headers: Dict[str, str]
    body: Optional[bytes]

    @property
    def is_json(self) -> bool:
        ct = self.headers.get("Content-Type", "")
        return "application/json" in ct

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def is_error(self) -> bool:
        return self.status_code >= 400


@dataclass
class TraceEntry:
    id: str
    request: HttpRequest
    response: HttpResponse
    metadata: Optional[Dict[str, Any]] = field(default=None)
    tags: list = field(default_factory=list)
    timestamp: Optional[str] = field(default=None)
