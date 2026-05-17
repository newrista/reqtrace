"""Lint HTTP trace entries for common issues and anti-patterns."""

from dataclasses import dataclass, field
from typing import List
from reqtrace.models import TraceEntry


@dataclass
class LintIssue:
    entry_id: str
    severity: str  # 'error', 'warning', 'info'
    code: str
    message: str


@dataclass
class LintResult:
    entry_id: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)


def _check_missing_content_type(entry: TraceEntry, issues: List[LintIssue]) -> None:
    if entry.request.body and not entry.request.content_type:
        issues.append(LintIssue(
            entry_id=entry.id,
            severity="warning",
            code="W001",
            message="Request has body but no Content-Type header",
        ))


def _check_large_body(entry: TraceEntry, issues: List[LintIssue], max_bytes: int = 1_048_576) -> None:
    body = entry.response.body or b""
    if isinstance(body, str):
        body = body.encode()
    if len(body) > max_bytes:
        issues.append(LintIssue(
            entry_id=entry.id,
            severity="info",
            code="I001",
            message=f"Response body exceeds {max_bytes} bytes ({len(body)} bytes)",
        ))


def _check_error_status_no_body(entry: TraceEntry, issues: List[LintIssue]) -> None:
    status = entry.response.status_code
    if status >= 400 and not entry.response.body:
        issues.append(LintIssue(
            entry_id=entry.id,
            severity="warning",
            code="W002",
            message=f"Error response ({status}) has no body",
        ))


def _check_auth_over_http(entry: TraceEntry, issues: List[LintIssue]) -> None:
    scheme = entry.request.url.split("://")[0].lower() if "://" in entry.request.url else "http"
    headers_lower = {k.lower(): v for k, v in entry.request.headers.items()}
    if scheme == "http" and ("authorization" in headers_lower or "cookie" in headers_lower):
        issues.append(LintIssue(
            entry_id=entry.id,
            severity="error",
            code="E001",
            message="Credentials sent over plain HTTP (not HTTPS)",
        ))


def lint_entry(entry: TraceEntry) -> LintResult:
    issues: List[LintIssue] = []
    _check_missing_content_type(entry, issues)
    _check_large_body(entry, issues)
    _check_error_status_no_body(entry, issues)
    _check_auth_over_http(entry, issues)
    return LintResult(entry_id=entry.id, issues=issues)


def lint_all(entries: List[TraceEntry]) -> List[LintResult]:
    return [lint_entry(e) for e in entries]


def lint_summary(results: List[LintResult]) -> dict:
    total_errors = sum(1 for r in results for i in r.issues if i.severity == "error")
    total_warnings = sum(1 for r in results for i in r.issues if i.severity == "warning")
    total_info = sum(1 for r in results for i in r.issues if i.severity == "info")
    return {
        "entries_checked": len(results),
        "entries_with_issues": sum(1 for r in results if r.issues),
        "errors": total_errors,
        "warnings": total_warnings,
        "info": total_info,
    }
