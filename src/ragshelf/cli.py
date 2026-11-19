"""Command-line interface: the `ragshelf` console script and `python -m ragshelf`.

This module only parses arguments and dispatches. Pipeline logic lives in the
library modules, and nothing here may load a model at import time.
"""

import argparse
import sys
from collections.abc import Sequence

# Exit code for a subcommand that exists but has no behavior yet.
EXIT_NOT_IMPLEMENTED = 2
EXIT_USAGE = 2

# Subcommand name -> one-line help. Each task that implements a subcommand
# replaces its placeholder arguments and handler.
SUBCOMMANDS = {
    "ingest": "Index the documents in the library.",
    "search": "Retrieve the chunks most relevant to a query.",
    "ask": "Answer a question with citations.",
    "eval": "Evaluate retrieval or answers on the gold set.",
    "inspect": "Show a document's metadata and heading outline from the parse cache.",
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


def _inspect(args: argparse.Namespace) -> int:
    if bool(args.doc_id) == args.all:
        print("ragshelf inspect: give exactly one of <doc_id> or --all", file=sys.stderr)
        return EXIT_USAGE
    # The cache is read only: no parser or model runtime is imported.
    from ragshelf.config import load_settings
    from ragshelf.documents import DocumentError, MetadataError, find_source, load_library, load_source
    from ragshelf.documents.render import format_inspect, format_table

    _robust_output()
    try:
        settings = load_settings()
        if args.all:
            results = load_library(settings)
            text, status = format_table(results), 1 if any(r.document is None for r in results) else 0
        else:
            source = find_source(settings, args.doc_id)
            text, status = format_inspect(load_source(settings, source)), 0
    except (DocumentError, MetadataError) as exc:
        print(f"ragshelf inspect: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        # Third-party exceptions can quote document text; report the type only.
        print(f"ragshelf inspect: {type(exc).__name__}; could not load the document", file=sys.stderr)
        return 1
    try:
        print(text)
    except OSError as exc:  # a closed pipe or a full disk is not a load failure
        print(f"ragshelf inspect: {type(exc).__name__}; could not write the output", file=sys.stderr)
        return 1
    return status


def _robust_output() -> None:
    # Redirected output defaults to the locale code page on Windows, which cannot hold every title or
    # author. Switch such a stream to UTF-8. A terminal keeps its encoding (the Windows NUL device
    # also reports itself as a terminal, with a code page). In every case an unencodable character is
    # replaced instead of failing the whole command.
    for stream in (sys.stdout, sys.stderr):
        if not hasattr(stream, "reconfigure"):
            continue
        utf8 = (stream.encoding or "").lower().replace("-", "") == "utf8"
        if utf8 or stream.isatty():
            stream.reconfigure(errors="replace")
        else:
            stream.reconfigure(encoding="utf-8", errors="replace")


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
        if name == "inspect":
            subparser.add_argument("doc_id", nargs="?", help="Library-relative path of the document.")
            subparser.add_argument("--all", action="store_true", help="Print a table for every library document.")
            subparser.set_defaults(handler=_inspect)
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
