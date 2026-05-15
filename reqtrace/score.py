"""Entry scoring — assigns a numeric quality/interest score to trace entries."""

from __future__ import annotations

from typing import List

from reqtrace.models import TraceEntry

# ---------------------------------------------------------------------------
# Individual scoring signals
# ---------------------------------------------------------------------------

SCORE_HAS_ERROR_STATUS = 30       # 4xx / 5xx responses are interesting
SCORE_HAS_REQUEST_BODY = 10       # entries with a body carry more info
SCORE_HAS_RESPONSE_BODY = 10
SCORE_SLOW_THRESHOLD_MS = 500     # responses slower than this get a bonus
SCORE_SLOW_BONUS = 20
SCORE_HAS_AUTH_HEADER = 15        # authenticated requests are notable
SCORE_HAS_QUERY_PARAMS = 5
SCORE_TAGGED = 5                  # bonus per tag (up to a cap)
SCORE_TAG_CAP = 20


def score_entry(entry: TraceEntry) -> int:
    """Return a non-negative integer score for *entry*.

    Higher scores indicate entries that are more likely to be interesting
    for review, debugging, or reporting.
    """
    points = 0

    # Error status codes
    status = entry.response.status_code
    if status >= 400:
        points += SCORE_HAS_ERROR_STATUS

    # Request body present
    if entry.request.has_body:
        points += SCORE_HAS_REQUEST_BODY

    # Response body present
    if entry.response.body:
        points += SCORE_HAS_RESPONSE_BODY

    # Slow response
    if entry.duration_ms is not None and entry.duration_ms >= SCORE_SLOW_THRESHOLD_MS:
        points += SCORE_SLOW_BONUS

    # Auth header present
    lower_headers = {k.lower(): v for k, v in entry.request.headers.items()}
    if "authorization" in lower_headers or "x-api-key" in lower_headers:
        points += SCORE_HAS_AUTH_HEADER

    # Query parameters
    if entry.request.query_params:
        points += SCORE_HAS_QUERY_PARAMS

    # Tags
    tags = (entry.metadata or {}).get("tags", [])
    points += min(len(tags) * SCORE_TAGGED, SCORE_TAG_CAP)

    return points


def score_all(entries: List[TraceEntry]) -> List[tuple]:
    """Return a list of (score, entry) tuples sorted by score descending."""
    scored = [(score_entry(e), e) for e in entries]
    scored.sort(key=lambda t: t[0], reverse=True)
    return scored


def top_scored(entries: List[TraceEntry], n: int = 10) -> List[TraceEntry]:
    """Return the top-*n* entries by score."""
    return [e for _, e in score_all(entries)[:n]]
