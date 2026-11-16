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


def test_module_entry_point_matches_the_console_script():
    result = subprocess.run(
        [sys.executable, "-m", "ragshelf", "search", "x"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "not implemented yet" in result.stderr
