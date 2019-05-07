"""pytest unit tests for pyfind
"""
from pathlib import Path

import pytest
from click.testing import CliRunner

import config
from pyfind import highlight_match, Search, textfile_to_list
from pyfind import cli, Match, is_notebook, search_file

LONG_TEXT = (
    "START Lorem ipsum dolor sit amet, consectetuer adipiscing elit. "
    "Maecenas porttitor congue massa. Fusce posuere, magna sed pulvinar "
    "ultricies, purus lectus malesuada libero, sit amet commodo magna eros "
    "quis urna. Nunc viverra imperdiet enim. Fusce est. Vivamus a tellus. "
    "Pellentesque habitant morbi tristique senectus et netus et malesuada fames "
    "ac turpis egestas. Proin pharetra nonummy pede. Mauris et orci. END"
)


def test_cli() -> None:
    """Test searching current folder.
    """
    runner = CliRunner()
    result = runner.invoke(cli, ["requests", "."])
    assert result.exit_code == 0
    assert "testdata.ipynb" in result.output
    assert "cell 1: import requests" in result.output


def test_cli_help() -> None:
    """Test the --help option.
    """
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert result.output.startswith("Usage: cli <options> searchfor <startdir>")


def test_cli_packages() -> None:
    """Test the *packages option.
    """
    runner = CliRunner()
    result = runner.invoke(cli, ["click.style('Some things'", "*packages"])
    assert result.exit_code == 0
    assert "site-packages\\click" in result.output
    assert "termui.py" in result.output


def test_cli_projects() -> None:
    """Test the *projects option.
    """
    runner = CliRunner()
    result = runner.invoke(cli, ["This comment is used by tests."])
    assert result.exit_code == 0
    assert "pyfind.py" in result.output
    assert "DO NOT REMOVE" in result.output


def test_cli_stdlib() -> None:
    """Test the *stdlib option.
    """
    runner = CliRunner()
    result = runner.invoke(cli, ["spam", "*stdlib"])
    assert result.exit_code == 0
    assert "hashlib.py" in result.output
    assert "Nobody inspects the spammish repetition" in result.output


def test_cli_txt() -> None:
    """Test searching .txt files.
    """
    runner = CliRunner()
    result = runner.invoke(cli, ["whatever", ".", "-ft=txt"])
    assert result.exit_code == 0
    assert "line 3: Should find" in result.output
    assert result.output.count("line 3:") == 1


def test_cli_txt_subfolder() -> None:
    """Test searching .txt files.
    """
    runner = CliRunner()
    result = runner.invoke(cli, ["whatever", ".", "-ft=txt", "-s"])
    assert result.exit_code == 0
    assert "line 3: Should find" in result.output
    assert result.output.count("line 3:") == 2


@pytest.mark.parametrize(
    "searchfor,maxchars,expected",
    [
        (
            "START",
            11,
            [("START", config.COLOR_MATCH_TEXT), (" Lorem", config.COLOR_MATCH_LINE)],
        ),
        (
            "Lorem",
            23,
            [
                ("START ", config.COLOR_MATCH_LINE),
                ("Lorem", config.COLOR_MATCH_TEXT),
                (" ipsum dolor", config.COLOR_MATCH_LINE),
            ],
        ),
        (
            "viverra",
            20,
            [
                (". Nunc ", config.COLOR_MATCH_LINE),
                ("viverra", config.COLOR_MATCH_TEXT),
                (" imper", config.COLOR_MATCH_LINE),
            ],
        ),
        (
            "orci",
            19,
            [
                ("Mauris et ", config.COLOR_MATCH_LINE),
                ("orci", config.COLOR_MATCH_TEXT),
                (". END", config.COLOR_MATCH_LINE),
            ],
        ),
        (
            "END",
            19,
            [
                ("Mauris et orci. ", config.COLOR_MATCH_LINE),
                ("END", config.COLOR_MATCH_TEXT),
            ],
        ),
    ],
)
def test_highlight_match(searchfor, maxchars, expected):
    """function: highlight_match()
    """
    assert highlight_match(LONG_TEXT, searchfor, maxchars) == expected


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("sample.ipynb", True),
        ("sample.py", False),
        (Path("sample.ipynb"), True),
        (Path("sample.py"), False),
    ],
)
def test_is_notebook(filename, expected):
    """function: is_notebook()
    """
    assert is_notebook(filename) == expected


def test_print_match(capsys):
    """method: Match.print_match()
    """
    line_of_text = 'Should find "whatever" on lines 3 and 4.'
    match = Match(
        file=Path("testdata.txt"), match=line_of_text, position=3, search_for="Whatever"
    )
    match.print_match()
    out, err = capsys.readouterr()
    assert out == f"    line 3: {line_of_text}\n"
    assert err == ""


def test_print_summary(capsys):
    """method: Search.print_summary()
    """
    searcher = Search("import", [".txt", ".ipynb"])
    searcher.search_folder(".", print_matches=False)
    searcher.print_summary()
    out, err = capsys.readouterr()
    assert out == f"  Searched: 1 folders, 2 files, 5 lines, 821 bytes\n"
    assert err == ""


@pytest.mark.parametrize(
    "filename, search_for, match, hits, lines, bytes",
    [
        (
            "testdata.py",
            "pathlib",
            Match(Path("testdata.py"), "import pathlib", 3, "pathlib"),
            1,
            3,
            57,
        ),
        (
            "testdata.txt",
            "Whatever",
            Match(
                Path("testdata.txt"),
                'Should find "whatever" on lines 3 and 4.',
                3,
                "Whatever",
            ),
            2,
            4,
            118,
        ),
        (
            "testdata.ipynb",
            "requests",
            Match(Path("testdata.ipynb"), "import requests", 1, "requests"),
            1,
            1,
            703,
        ),
    ],
)
def test_search_file(filename, search_for, match, hits, lines, bytes):
    """function: search_file()
    """
    search_results = search_file(filename, search_for)
    assert search_results[0][0].file == match.file
    assert search_results[0][0].match == match.match
    assert search_results[0][0].position == match.position
    assert search_results[0][0].search_for == match.search_for
    assert len(search_results[0]) == hits
    assert search_results[1] == lines
    assert search_results[2] == bytes


def test_search_folder():
    """method: Search.search_folder()
    """
    searcher = Search("import", [".txt", ".ipynb"])
    matches = searcher.search_folder(".", print_matches=False)
    assert len(matches) == 2
    assert "testdata.ipynb" in [str(match.file) for match in matches]
    assert "testdata.txt" in [str(match.file) for match in matches]


def test_textfile_to_list():
    """function: textfile_to_list()
    """
    testdata = textfile_to_list("testdata.txt")
    assert len(testdata) == 4
    assert testdata[0] == "Sample text file for use in pyfind unit tests."
    assert testdata[3] == "whatever"


if __name__ == "__main__":
    pytest.main()  # run all tests
