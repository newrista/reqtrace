"""Data models for reqtrace."""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class HttpRequest:
    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[bytes] = None
    query_params: Dict[str, str] = field(default_factory=dict)

    @property
    def path(self) -> str:
        from urllib.parse import urlparse
        return urlparse(self.url).path

    def is_json(self) -> bool:
        ct = self.headers.get("Content-Type", "")
        return "application/json" in ct

    def has_body(self) -> bool:
        return self.body is not None and len(self.body) > 0


@dataclass
class HttpResponse:
    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[bytes] = None

    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def is_json(self) -> bool:
        ct = self.headers.get("Content-Type", "")
        return "application/json" in ct


@dataclass
class TraceEntry:
    id: str
    request: HttpRequest
    response: HttpResponse
    timestamp: str
    duration_ms: Optional[float] = None
    tags: List[str] = field(default_factory=list)

    def _replace(self, **kwargs) -> "TraceEntry":
        """Return a copy with fields replaced."""
        import dataclasses
        return dataclasses.replace(self, **kwargs)
