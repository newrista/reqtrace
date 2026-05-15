"""CLI sub-commands for chain analysis."""

import argparse
import json
from reqtrace.storage import TraceStore
from reqtrace.chain import (
    group_by_session,
    group_by_path_prefix,
    find_chains,
    chain_summary,
)


def build_chain_parser(subparsers=None):
    if subparsers is None:
        parser = argparse.ArgumentParser(description="Chain analysis commands")
        sub = parser.add_subparsers(dest="chain_cmd")
    else:
        parser = subparsers.add_parser("chain", help="Analyse request chains")
        sub = parser.add_subparsers(dest="chain_cmd")

    # session grouping
    p_session = sub.add_parser("session", help="Group requests by session header")
    p_session.add_argument("--header", default="X-Session-Id", help="Session header name")

    # path-prefix grouping
    p_prefix = sub.add_parser("prefix", help="Group requests by path prefix")
    p_prefix.add_argument("--depth", type=int, default=1, help="Number of path segments")

    # chain detection
    p_detect = sub.add_parser("detect", help="Detect request chains by timing")
    p_detect.add_argument("--gap", type=float, default=2.0, help="Max gap in seconds")

    return parser


def run_chain(store: TraceStore, args) -> None:
    entries = store.get_all()
    cmd = getattr(args, "chain_cmd", None)

    if cmd == "session":
        groups = group_by_session(entries, session_header=args.header)
        output = {k: len(v) for k, v in groups.items()}
        print(json.dumps(output, indent=2))

    elif cmd == "prefix":
        groups = group_by_path_prefix(entries, depth=args.depth)
        output = {k: len(v) for k, v in groups.items()}
        print(json.dumps(output, indent=2))

    elif cmd == "detect":
        chains = find_chains(entries, gap_seconds=args.gap)
        summaries = chain_summary(chains)
        print(json.dumps(summaries, indent=2))

    else:
        print("No chain sub-command specified. Use: session | prefix | detect")
