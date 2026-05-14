"""Tests for reqtrace.reporter — OpenAPI report generation."""

import json
import pytest

from reqtrace.models import HttpRequest, HttpResponse, TraceEntry
from reqtrace.storage import TraceStore
from reqtrace.reporter import generate_openapi_report, report_to_json


def _make_entry(
    method="GET",
    path="/api/items",
    query_string="",
    req_body=b"",
    content_type="",
    status_code=200,
    reason="OK",
    resp_content_type="application/json",
):
    request = HttpRequest(
        method=method,
        path=path,
        query_string=query_string,
        headers={},
        body=req_body,
        content_type=content_type,
    )
    response = HttpResponse(
        status_code=status_code,
        reason=reason,
        headers={},
        body=b"{}",
        content_type=resp_content_type,
    )
    return TraceEntry(request=request, response=response)


def test_report_structure():
    store = TraceStore()
    store.add(_make_entry())
    report = generate_openapi_report(store)

    assert report["openapi"] == "3.0.0"
    assert "info" in report
    assert "paths" in report


def test_report_contains_path_and_method():
    store = TraceStore()
    store.add(_make_entry(method="POST", path="/api/orders"))
    report = generate_openapi_report(store)

    assert "/api/orders" in report["paths"]
    assert "post" in report["paths"]["/api/orders"]


def test_report_query_parameters():
    store = TraceStore()
    store.add(_make_entry(query_string="page=1&limit=10"))
    report = generate_openapi_report(store)

    params = report["paths"]["/api/items"]["get"]["parameters"]
    param_names = [p["name"] for p in params]
    assert "page" in param_names
    assert "limit" in param_names


def test_report_request_body():
    store = TraceStore()
    store.add(_make_entry(method="POST", req_body=b'{"x":1}', content_type="application/json"))
    report = generate_openapi_report(store)

    op = report["paths"]["/api/items"]["post"]
    assert "requestBody" in op
    assert "application/json" in op["requestBody"]["content"]


def test_report_response_status():
    store = TraceStore()
    store.add(_make_entry(status_code=201, reason="Created"))
    report = generate_openapi_report(store)

    responses = report["paths"]["/api/items"]["get"]["responses"]
    assert "201" in responses
    assert responses["201"]["description"] == "Created"


def test_report_to_json_is_valid():
    store = TraceStore()
    store.add(_make_entry())
    raw = report_to_json(store, title="Test API", version="1.0.0")
    data = json.loads(raw)

    assert data["info"]["title"] == "Test API"
    assert data["info"]["version"] == "1.0.0"


def test_empty_store_produces_empty_paths():
    store = TraceStore()
    report = generate_openapi_report(store)
    assert report["paths"] == {}
