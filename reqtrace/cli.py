"""CLI entry point for reqtrace."""

from __future__ import annotations

import argparse
import json
import sys

from reqtrace.exporter import export_json
from reqtrace.filter import (
    apply_filters,
    filter_by_method,
    filter_by_path,
    filter_by_status,
)
from reqtrace.storage import TraceStore
from reqtrace.summary import summarize, top_paths
from reqtrace.validate import validate_all


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reqtrace",
        description="Lightweight HTTP request logger and inspector.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # summary
    sub.add_parser("summary", help="Print traffic summary.")

    # top-paths
    tp = sub.add_parser("top-paths", help="Show top N requested paths.")
    tp.add_argument("-n", type=int, default=5)

    # filter
    f_cmd = sub.add_parser("filter", help="Filter and print entries.")
    f_cmd.add_argument("--method", default=None)
    f_cmd.add_argument("--path", default=None)
    f_cmd.add_argument("--status", type=int, default=None)

    # export
    ex = sub.add_parser("export", help="Export entries to JSON.")
    ex.add_argument("--output", default="-", help="Output file (- for stdout).")

    # validate
    v_cmd = sub.add_parser("validate", help="Validate entries against OpenAPI schema.")
    v_cmd.add_argument("schema", help="Path to OpenAPI JSON schema file.")

    return parser


def run(store: TraceStore, argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    entries = store.get_all()

    if args.command == "summary":
        stats = summarize(entries)
        for key, value in stats.items():
            print(f"{key}: {value}")

    elif args.command == "top-paths":
        for path, count in top_paths(entries, n=args.n):
            print(f"{count:>6}  {path}")

    elif args.command == "filter":
        if args.method:
            entries = filter_by_method(entries, args.method)
        if args.path:
            entries = filter_by_path(entries, args.path)
        if args.status:
            entries = filter_by_status(entries, args.status)
        for e in entries:
            print(e.summary())

    elif args.command == "export":
        data = export_json(entries)
        if args.output == "-":
            print(data)
        else:
            with open(args.output, "w") as fh:
                fh.write(data)

    elif args.command == "validate":
        with open(args.schema) as fh:
            openapi = json.load(fh)
        results = validate_all(entries, openapi)
        invalid = [r for r in results if not r.is_valid]
        if not invalid:
            print("All entries valid.")
        else:
            for r in invalid:
                print(f"INVALID [{r.entry_id}] {r.method} {r.path}")
                for err in r.errors:
                    print(f"  - {err}")
            sys.exit(1)
