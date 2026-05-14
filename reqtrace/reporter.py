"""Generate structured OpenAPI-compatible reports from captured traces."""

from __future__ import annotations

import json
from typing import Any

from reqtrace.storage import TraceStore


def _method_entry(entry: Any) -> dict:
    """Build an OpenAPI path-item method object from a trace entry."""
    request = entry.request
    response = entry.response

    operation: dict[str, Any] = {
        "summary": f"{request.method} {request.path}",
        "parameters": [],
        "responses": {},
    }

    # Query parameters
    if request.query_string:
        for param in request.query_string.split("&"):
            if "=" in param:
                name, _, _ = param.partition("=")
            else:
                name = param
            operation["parameters"].append(
                {"name": name, "in": "query", "schema": {"type": "string"}}
            )

    # Request body hint
    if request.body and request.content_type:
        operation["requestBody"] = {
            "content": {
                request.content_type: {
                    "schema": {"type": "object"}
                }
            }
        }

    # Response
    if response:
        status = str(response.status_code)
        response_entry: dict[str, Any] = {
            "description": response.reason or "OK"
        }
        if response.content_type:
            response_entry["content"] = {
                response.content_type: {"schema": {"type": "object"}}
            }
        operation["responses"][status] = response_entry
    else:
        operation["responses"]["200"] = {"description": "OK"}

    return operation


def generate_openapi_report(store: TraceStore, title: str = "reqtrace Report", version: str = "0.1.0") -> dict:
    """Return an OpenAPI 3.0 skeleton document built from all stored traces."""
    paths: dict[str, Any] = {}

    for entry in store.get_all():
        path = entry.request.path or "/"
        method = entry.request.method.lower()
        paths.setdefault(path, {})
        paths[path][method] = _method_entry(entry)

    return {
        "openapi": "3.0.0",
        "info": {"title": title, "version": version},
        "paths": paths,
    }


def report_to_json(store: TraceStore, **kwargs: Any) -> str:
    """Serialize the OpenAPI report to a JSON string."""
    return json.dumps(generate_openapi_report(store, **kwargs), indent=2)
