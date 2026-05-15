"""CLI subcommands for inspecting transform operations on stored trace entries."""

import argparse
import json
from reqtrace.storage import TraceStore
from reqtrace.transform import (
    set_request_header,
    remove_request_header,
    replace_request_body,
)


def build_transform_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register 'transform' subcommands onto an existing subparser group."""
    t = subparsers.add_parser("transform", help="Transform a stored trace entry")
    t_sub = t.add_subparsers(dest="transform_cmd", required=True)

    # set-header
    sh = t_sub.add_parser("set-header", help="Set a request header on an entry")
    sh.add_argument("entry_id", help="ID of the trace entry")
    sh.add_argument("key", help="Header name")
    sh.add_argument("value", help="Header value")

    # remove-header
    rh = t_sub.add_parser("remove-header", help="Remove a request header from an entry")
    rh.add_argument("entry_id", help="ID of the trace entry")
    rh.add_argument("key", help="Header name to remove")

    # set-body
    sb = t_sub.add_parser("set-body", help="Replace the request body of an entry")
    sb.add_argument("entry_id", help="ID of the trace entry")
    sb.add_argument("body", help="New body content (string)")


def run_transform(args: argparse.Namespace, store: TraceStore) -> None:
    """Execute the transform subcommand described by args."""
    entry = store.get_by_id(args.entry_id)
    if entry is None:
        print(f"Error: entry '{args.entry_id}' not found.")
        return

    if args.transform_cmd == "set-header":
        result = set_request_header(entry, args.key, args.value)
        print(f"[set-header] {args.key}: {args.value}")
        print(json.dumps(dict(result.request.headers), indent=2))

    elif args.transform_cmd == "remove-header":
        result = remove_request_header(entry, args.key)
        removed = args.key not in result.request.headers
        print(f"[remove-header] '{args.key}' removed: {removed}")
        print(json.dumps(dict(result.request.headers), indent=2))

    elif args.transform_cmd == "set-body":
        new_body = args.body.encode("utf-8")
        result = replace_request_body(entry, new_body)
        body_preview = result.request.body.decode("utf-8", errors="replace") if result.request.body else ""
        print(f"[set-body] body updated ({len(new_body)} bytes)")
        print(body_preview)

    else:
        print(f"Unknown transform command: {args.transform_cmd}")
