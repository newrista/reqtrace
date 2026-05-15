"""CLI entry point for reqtrace."""

import argparse
import json
import sys

from reqtrace.storage import TraceStore
from reqtrace.summary import summarize, top_paths
from reqtrace.filter import (
    filter_by_method,
    filter_by_status_range,
    filter_by_content_type,
)
from reqtrace.exporter import export_json, export_har
from reqtrace.redact import redact_entry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reqtrace",
        description="Lightweight HTTP request logger and inspector.",
    )
    sub = parser.add_subparsers(dest="command")

    # summary
    sub.add_parser("summary", help="Print traffic summary")

    # top-paths
    tp = sub.add_parser("top-paths", help="List most frequent paths")
    tp.add_argument("--limit", type=int, default=5)

    # filter
    f = sub.add_parser("filter", help="Filter entries")
    f.add_argument("--method", type=str)
    f.add_argument("--status-min", type=int)
    f.add_argument("--status-max", type=int)
    f.add_argument("--content-type", type=str)

    # export
    ex = sub.add_parser("export", help="Export traces")
    ex.add_argument("--format", choices=["json", "har"], default="json")
    ex.add_argument("--redact", action="store_true", help="Redact sensitive fields")
    ex.add_argument("--output", type=str, default=None)

    return parser


def run(store: TraceStore, args=None, out=None):
    if out is None:
        out = sys.stdout

    parser = build_parser()
    parsed = parser.parse_args(args)

    if parsed.command == "summary":
        stats = summarize(store.get_all())
        for k, v in stats.items():
            out.write(f"{k}: {v}\n")

    elif parsed.command == "top-paths":
        paths = top_paths(store.get_all(), limit=parsed.limit)
        for path, count in paths:
            out.write(f"{path}: {count}\n")

    elif parsed.command == "filter":
        entries = store.get_all()
        if parsed.method:
            entries = filter_by_method(entries, parsed.method)
        if parsed.status_min is not None and parsed.status_max is not None:
            entries = filter_by_status_range(entries, parsed.status_min, parsed.status_max)
        if parsed.content_type:
            entries = filter_by_content_type(entries, parsed.content_type)
        for e in entries:
            out.write(e.summary_line() + "\n")

    elif parsed.command == "export":
        entries = store.get_all()
        if getattr(parsed, "redact", False):
            entries = [redact_entry(e) for e in entries]
        if parsed.format == "har":
            data = export_har(entries)
        else:
            data = export_json(entries)
        if parsed.output:
            with open(parsed.output, "w") as f:
                f.write(data)
        else:
            out.write(data + "\n")

    else:
        parser.print_help(out)
