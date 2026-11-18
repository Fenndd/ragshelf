"""Command-line interface: the `ragshelf` console script and `python -m ragshelf`.

This module only parses arguments and dispatches. Pipeline logic lives in the
library modules, and nothing here may load a model at import time.
"""

import argparse
import sys
from collections.abc import Sequence

# Exit code for a subcommand that exists but has no behavior yet.
EXIT_NOT_IMPLEMENTED = 2

# Subcommand name -> one-line help. Each task that implements a subcommand
# replaces its placeholder arguments and handler.
SUBCOMMANDS = {
    "ingest": "Index the documents in the library.",
    "search": "Retrieve the chunks most relevant to a query.",
    "ask": "Answer a question with citations.",
    "eval": "Evaluate retrieval or answers on the gold set.",
}


def _not_implemented(args: argparse.Namespace) -> int:
    print(f"ragshelf {args.command}: not implemented yet", file=sys.stderr)
    return EXIT_NOT_IMPLEMENTED


def _ingest(args: argparse.Namespace) -> int:
    if not args.parse_only:
        return _not_implemented(args)
    from ragshelf.config import load_settings
    from ragshelf.parse import parse_library

    try:
        report = parse_library(load_settings())
    except Exception as exc:
        # Parser exceptions can contain source text or secrets; report the type.
        print(f"ragshelf ingest: {type(exc).__name__}; parse batch failed", file=sys.stderr)
        return 1
    for item in report.outcomes:
        label = {"hit": "cache hit", "parsed": "cache miss: parsed", "failed": "failed"}[item.status]
        print(f"{label}: {item.source.doc_id}" + (f" ({item.error})" if item.error else ""))
    print(f"Parse complete: {report.hits} cache hits, {report.parsed} parsed, {report.failed} failed.")
    return 1 if report.failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ragshelf",
        description="Retrieval-augmented generation over a personal library of documents.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>", required=True)
    for name, help_text in SUBCOMMANDS.items():
        subparser = subparsers.add_parser(name, help=help_text, description=help_text)
        if name == "ingest":
            subparser.add_argument("--parse-only", action="store_true", help="Scan and cache parsing without indexing.")
            subparser.set_defaults(handler=_ingest)
            continue
        # Placeholder until the subcommand defines its arguments: takes positional
        # arguments and whatever follows the first one. An unknown option before
        # the first positional is still an argparse usage error.
        subparser.add_argument("args", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
        subparser.set_defaults(handler=_not_implemented)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
