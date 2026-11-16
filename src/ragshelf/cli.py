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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ragshelf",
        description="Retrieval-augmented generation over a personal library of documents.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>", required=True)
    for name, help_text in SUBCOMMANDS.items():
        subparser = subparsers.add_parser(name, help=help_text, description=help_text)
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
