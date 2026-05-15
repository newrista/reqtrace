"""CLI subcommands for running assertions against stored trace entries."""

import argparse
import json
from reqtrace.storage import TraceStore
from reqtrace.assert_response import assert_all, all_passed


def build_assert_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("assert", help="Run assertions against captured entries")
    p.add_argument("--status", type=int, default=None, help="Expected HTTP status code")
    p.add_argument(
        "--header",
        action="append",
        dest="headers",
        metavar="NAME",
        default=[],
        help="Assert response header is present (repeatable)",
    )
    p.add_argument(
        "--body-contains",
        default=None,
        metavar="TEXT",
        help="Assert response body contains TEXT",
    )
    p.add_argument(
        "--id",
        dest="entry_id",
        default=None,
        help="Run assertions on a single entry by ID",
    )
    p.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        help="Output results as JSON",
    )
    p.set_defaults(func=run_assert)


def run_assert(args: argparse.Namespace, store: TraceStore) -> None:
    if args.entry_id:
        entry = store.get_by_id(args.entry_id)
        entries = [entry] if entry else []
    else:
        entries = store.get_all()

    if not entries:
        print("No entries found.")
        return

    all_results = []
    for entry in entries:
        results = assert_all(
            entry,
            status=args.status,
            headers_present=args.headers,
            body_contains=args.body_contains,
        )
        all_results.extend(results)

    if args.output_json:
        output = [
            {"entry_id": r.entry_id, "passed": r.passed, "message": r.message}
            for r in all_results
        ]
        print(json.dumps(output, indent=2))
        return

    passed = 0
    failed = 0
    for r in all_results:
        status_icon = "✓" if r.passed else "✗"
        print(f"  [{status_icon}] {r.entry_id[:8]}  {r.message}")
        if r.passed:
            passed += 1
        else:
            failed += 1

    print(f"\n{passed} passed, {failed} failed out of {len(all_results)} assertion(s).")
