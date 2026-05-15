"""CLI entry point for reqtrace."""

import argparse
import json
import sys
from reqtrace.storage import TraceStore
from reqtrace.summary import summarize, top_paths
from reqtrace.filter import (
    filter_by_method, filter_by_path, filter_by_status, filter_by_status_range
)
from reqtrace.exporter import export_json, export_har
from reqtrace.timeline import sort_by_time, slowest, timeline_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reqtrace", description="HTTP request tracer")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("summary", help="Show summary of captured requests")

    top = sub.add_parser("top-paths", help="Show most frequent paths")
    top.add_argument("--n", type=int, default=5)

    fil = sub.add_parser("filter", help="Filter entries")
    fil.add_argument("--method", type=str)
    fil.add_argument("--path", type=str)
    fil.add_argument("--status", type=int)
    fil.add_argument("--min-status", type=int)
    fil.add_argument("--max-status", type=int)

    exp = sub.add_parser("export", help="Export entries")
    exp.add_argument("--format", choices=["json", "har"], default="json")

    tl = sub.add_parser("timeline", help="Show timeline summary")
    tl.add_argument("--slowest", type=int, default=0, dest="slowest_n",
                    help="Show N slowest entries")

    return parser


def run(store: TraceStore, argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    entries = store.get_all()

    if args.command == "summary":
        result = summarize(entries)
        print(json.dumps(result, indent=2))

    elif args.command == "top-paths":
        result = top_paths(entries, n=args.n)
        for path, count in result:
            print(f"{count:>6}  {path}")

    elif args.command == "filter":
        if args.method:
            entries = filter_by_method(entries, args.method)
        if args.path:
            entries = filter_by_path(entries, args.path)
        if args.status:
            entries = filter_by_status(entries, args.status)
        if args.min_status and args.max_status:
            entries = filter_by_status_range(entries, args.min_status, args.max_status)
        print(json.dumps([e.id for e in entries], indent=2))

    elif args.command == "export":
        if args.format == "json":
            print(export_json(entries))
        else:
            print(export_har(entries))

    elif args.command == "timeline":
        if args.slowest_n > 0:
            result = slowest(entries, n=args.slowest_n)
            for e in result:
                print(f"{e.id}  {e.duration}ms  {e.request.method} {e.request.path}")
        else:
            result = timeline_summary(entries)
            print(json.dumps(result, indent=2))

    else:
        parser.print_help()
        sys.exit(1)
