"""Command-line interface for reqtrace inspection utilities."""

import argparse
import json
import sys

from reqtrace.storage import TraceStore
from reqtrace.filter import search_entries
from reqtrace.summary import summarize, top_paths
from reqtrace.exporter import export_json, export_har


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reqtrace",
        description="Inspect and export captured HTTP traces.",
    )
    sub = parser.add_subparsers(dest="command")

    # summary command
    sub.add_parser("summary", help="Print summary statistics of captured traces.")

    # top-paths command
    top = sub.add_parser("top-paths", help="Print the most frequently requested paths.")
    top.add_argument("--n", type=int, default=5, help="Number of paths to show.")

    # filter command
    flt = sub.add_parser("filter", help="Filter traces and print as JSON.")
    flt.add_argument("--method", type=str, default=None)
    flt.add_argument("--path-prefix", type=str, default=None)
    flt.add_argument("--status", type=int, default=None)
    flt.add_argument("--content-type", type=str, default=None)

    # export command
    exp = sub.add_parser("export", help="Export traces to JSON or HAR format.")
    exp.add_argument("--format", choices=["json", "har"], default="json")
    exp.add_argument("--output", type=str, default=None, help="Output file path.")

    return parser


def run(store: TraceStore, argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    entries = store.get_all()

    if args.command == "summary":
        print(json.dumps(summarize(entries), indent=2))

    elif args.command == "top-paths":
        print(json.dumps(top_paths(entries, n=args.n), indent=2))

    elif args.command == "filter":
        results = search_entries(
            entries,
            method=args.method,
            path_prefix=args.path_prefix,
            status_code=args.status,
            content_type=args.content_type,
        )
        print(json.dumps([e.__dict__ for e in results], indent=2, default=str))

    elif args.command == "export":
        output = export_json(entries) if args.format == "json" else export_har(entries)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
        else:
            print(output)

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    from reqtrace.storage import TraceStore as _Store
    sys.exit(run(_Store()))
