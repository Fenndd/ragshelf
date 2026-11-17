"""Entry point for `python -m ragshelf`."""

from ragshelf.cli import main

# Guarded so that importing this module (for example while walking the
# package) does not run the CLI.
if __name__ == "__main__":
    raise SystemExit(main())
