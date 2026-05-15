"""Validate recorded trace entries against an OpenAPI schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from reqtrace.models import TraceEntry


@dataclass
class ValidationResult:
    entry_id: str
    path: str
    method: str
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


def _resolve_schema_for_path(
    openapi: dict[str, Any], path: str, method: str
) -> dict[str, Any] | None:
    """Return the operation object for a given path and method, or None."""
    paths = openapi.get("paths", {})
    path_item = paths.get(path)
    if path_item is None:
        return None
    return path_item.get(method.lower())


def _validate_status(operation: dict[str, Any], status: int) -> list[str]:
    errors: list[str] = []
    responses = operation.get("responses", {})
    allowed = {int(k) for k in responses if k != "default"}
    if allowed and status not in allowed:
        errors.append(
            f"Response status {status} not listed in schema "
            f"(allowed: {sorted(allowed)})"
        )
    return errors


def _validate_content_type(
    operation: dict[str, Any], content_type: str | None
) -> list[str]:
    errors: list[str] = []
    request_body = operation.get("requestBody", {})
    if not request_body:
        return errors
    allowed_types = set(request_body.get("content", {}).keys())
    if allowed_types and content_type:
        base_ct = content_type.split(";")[0].strip()
        if base_ct not in allowed_types:
            errors.append(
                f"Content-Type '{base_ct}' not in schema "
                f"(allowed: {sorted(allowed_types)})"
            )
    return errors


def validate_entry(
    entry: TraceEntry, openapi: dict[str, Any]
) -> ValidationResult:
    """Validate a single trace entry against an OpenAPI document."""
    path = entry.request.path
    method = entry.request.method
    result = ValidationResult(entry_id=entry.id, path=path, method=method)

    operation = _resolve_schema_for_path(openapi, path, method)
    if operation is None:
        result.errors.append(
            f"Path '{path}' with method '{method}' not found in schema"
        )
        return result

    if entry.response is not None:
        result.errors.extend(_validate_status(operation, entry.response.status_code))
        ct = entry.request.headers.get("content-type")
        result.errors.extend(_validate_content_type(operation, ct))

    return result


def validate_all(
    entries: list[TraceEntry], openapi: dict[str, Any]
) -> list[ValidationResult]:
    """Validate all entries and return a list of results."""
    return [validate_entry(e, openapi) for e in entries]
