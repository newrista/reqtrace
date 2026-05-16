"""CLI sub-commands for snapshot save / load / merge."""

from __future__ import annotations

import argparse
import sys

from reqtrace.snapshot import load_snapshot, merge_snapshots, save_snapshot
from reqtrace.storage import TraceStore


def build_snapshot_parser(subparsers=None):
    if subparsers is None:
        parser = argparse.ArgumentParser(prog="reqtrace-snapshot")
        sub = parser.add_subparsers(dest="snapshot_cmd")
    else:
        parser = subparsers.add_parser("snapshot", help="Snapshot management")
        sub = parser.add_subparsers(dest="snapshot_cmd")

    save_p = sub.add_parser("save", help="Save current trace store to a file")
    save_p.add_argument("output", help="Destination .json file")

    load_p = sub.add_parser("load", help="Load a snapshot and print entry count")
    load_p.add_argument("input", help="Source .json snapshot file")

    merge_p = sub.add_parser("merge", help="Merge multiple snapshots into one")
    merge_p.add_argument("inputs", nargs="+", help="Source snapshot files")
    merge_p.add_argument("--output", required=True, help="Destination .json file")

    return parser


def run_snapshot(args, store: TraceStore, out=None):
    if out is None:
        out = sys.stdout

    cmd = getattr(args, "snapshot_cmd", None)

    if cmd == "save":
        save_snapshot(store, args.output)
        out.write(f"Saved {len(store.get_all())} entries to {args.output}\n")

    elif cmd == "load":
        loaded = load_snapshot(args.input)
        entries = loaded.get_all()
        out.write(f"Loaded {len(entries)} entries from {args.input}\n")
        for e in entries:
            out.write(f"  [{e.id}] {e.request.method} {e.request.url}\n")

    elif cmd == "merge":
        merged = merge_snapshots(args.inputs)
        save_snapshot(merged, args.output)
        out.write(
            f"Merged {len(merged.get_all())} unique entries into {args.output}\n"
        )

    else:
        out.write("No snapshot sub-command given. Use save / load / merge.\n")
