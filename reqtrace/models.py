"""Core data models for reqtrace."""

from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse, parse_qs


@dataclass
class HttpRequest:
    method: str
    url: str
    headers: Dict[str, str]
    body: Optional[str] = None

    @property
    def path(self) -> str:
        return urlparse(self.url).path

    @property
    def query_params(self) -> Dict[str, List[str]]:
        return parse_qs(urlparse(self.url).query)

    @property
    def is_json(self) -> bool:
        ct = self.headers.get("Content-Type", self.headers.get("content-type", ""))
        return "application/json" in ct

    @property
    def has_body(self) -> bool:
        return self.body is not None and len(self.body) > 0

    @property
    def host(self) -> str:
        return urlparse(self.url).netloc

    @property
    def scheme(self) -> str:
        return urlparse(self.url).scheme


@dataclass
class HttpResponse:
    status_code: int
    headers: Dict[str, str]
    body: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def is_error(self) -> bool:
        return self.status_code >= 400

    @property
    def content_type(self) -> str:
        return self.headers.get("Content-Type", self.headers.get("content-type", ""))


@dataclass
class TraceEntry:
    request: HttpRequest
    response: HttpResponse
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, str] = field(default_factory=dict)
