import importlib
import subprocess
import sys

import pytest

from ragshelf.cli import main

SUBCOMMANDS = ["ingest", "search", "ask", "eval"]


def test_help_lists_the_subcommands(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])

    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    for name in SUBCOMMANDS:
        assert name in out


@pytest.mark.parametrize("argv", [[name] for name in SUBCOMMANDS] + [["search", "x"]])
def test_subcommand_is_not_implemented(argv, capsys):
    assert main(argv) == 2
    assert "not implemented yet" in capsys.readouterr().err


def test_missing_subcommand_is_a_usage_error(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([])

    assert excinfo.value.code == 2
    assert "usage:" in capsys.readouterr().err


def test_unknown_subcommand_is_a_usage_error(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["nonsense"])

    assert excinfo.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_importing_the_module_entry_point_does_not_run_the_cli():
    # A package walk imports every module; that must not start the CLI.
    importlib.import_module("ragshelf.__main__")


def test_module_entry_point_matches_the_console_script():
    result = subprocess.run(
        [sys.executable, "-m", "ragshelf", "search", "x"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "not implemented yet" in result.stderr


def test_parse_only_caches_text_and_returns_errors(tmp_path, monkeypatch, capsys):
    library = tmp_path / "library"
    library.mkdir()
    (library / "note.txt").write_text("Synthetic document", encoding="utf-8")
    monkeypatch.setenv("RAGSHELF_PATHS__LIBRARY", str(library))
    monkeypatch.setenv("RAGSHELF_PATHS__CACHE", str(tmp_path / "cache"))
    assert main(["ingest", "--parse-only"]) == 0
    assert "0 cache hits, 1 parsed, 0 failed" in capsys.readouterr().out
    assert main(["ingest", "--parse-only"]) == 0
    assert "1 cache hits, 0 parsed, 0 failed" in capsys.readouterr().out
    (library / "bad.txt").write_bytes(b"\xff")
    assert main(["ingest", "--parse-only"]) == 1
    assert "1 failed" in capsys.readouterr().out


def test_parse_only_missing_library_returns_nonzero(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RAGSHELF_PATHS__LIBRARY", str(tmp_path / "missing"))
    monkeypatch.setenv("RAGSHELF_PATHS__CACHE", str(tmp_path / "cache"))
    assert main(["ingest", "--parse-only"]) == 1
    assert "FileNotFoundError" in capsys.readouterr().err
