"""pyfind - command line search utility
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import site
import sys
from typing import List, Tuple, Union

import click

import config

CONTEXT_SETTINGS: dict = dict(help_option_names=["-h", "--help"])

# This comment is used by tests. DO NOT REMOVE


@click.argument("startdir", default="*projects", metavar="<startdir>")
@click.argument("searchfor", metavar="searchfor")
@click.command(context_settings=CONTEXT_SETTINGS, options_metavar="<options>")
@click.option(
    "-s",
    "--subfolders",
    default=False,
    help="search subfolders as well",
    is_flag=True,
    metavar="",
)
@click.option(
    "-ft",
    "--filetypes",
    metavar="<str>",
    help="File types to search. Multiple types may "
    + "be delimited with /. Default: -ft=py/ipynb",
)
@click.version_option(version="1.1", prog_name="PyFind")
def cli(searchfor: str, startdir: str, filetypes: str, subfolders: bool) -> None:
    """\b
    _______________         searchfor: text to search for (required)
     |___|___|___|          startdir:  folder to search, or one of the options below
       |___|___|            *projects = project folders (defined in projects.txt)
         |___|              *stdlib   = Python standard library
           |                *packages = installed packages in current environment
    """
    # Note that Click uses the above docstring for the help screen.

    typelist: List[str]
    if filetypes:
        typelist = ["." + _.lower() for _ in filetypes.split("/")]
    else:
        typelist = [".py", ".ipynb"]
    searcher = Search(search_for=searchfor, file_types=typelist)

    if startdir.lower().startswith("*project"):
        # special case for *projects option
        pyfind_folder: Path = Path(__file__).resolve().parent
        projects_file: Path = Path.joinpath(pyfind_folder, "projects.txt")
        if not projects_file.is_file():
            click.echo(click.style(f"FILE NOT FOUND: {projects_file}", fg="red"))
            return
        for project_folder in textfile_to_list(projects_file):
            searcher.search_folder(project_folder, subdirs=subfolders)
        searcher.print_summary()
        return

    search_root: Path
    if startdir.lower().startswith("*package"):
        # search installed packages source code
        search_root = Path(site.getsitepackages()[-1])
        subfolders = True  # force subfolder search for *packages option
    elif startdir.lower().startswith("*stdlib"):
        # search Python standard library source code
        search_root = Path(sys.exec_prefix).joinpath("Lib")
    else:
        # An explicit search folder was specified on the command line.
        search_root = Path(startdir)

    searcher.search_folder(search_root, subdirs=subfolders)
    searcher.print_summary()


class Match:
    """Stores a single match found in a search.
    """

    def __init__(self, file: Path, match: str, position: int, search_for: str) -> None:
        """Constructor, initializes properties.

        Args:
            file: the file that was searched, as a pathlib.Path
            match: the line of text where a match was found
            position: the position of the match within the file. Either a line
                number, or a cell number (for notebook files).
            search_for: the search text that was found.
        Returns:
            None
        """
        self.file = file
        self.match = match
        self.position = position
        self.search_for = search_for

    def print_match(self) -> None:
        """Prints the match to the console.
        """
        prefix = f"{'cell' if is_notebook(self.file) else 'line'} {self.position}: ".rjust(
            config.PREFIX_LENGTH
        )

        # chars = the maximum number of characters of self.match to be printed
        chars: int = get_console_width() - len(prefix)
        # to color-highlight the matched text, break the line into sections
        sections: List[Tuple] = highlight_match(self.match, self.search_for, chars)

        click.echo("\r", nl=False)  # reset console to start of line

        # print the prefix, with nl=False to print the sections on the same line
        click.echo(click.style(prefix, fg=config.COLOR_MATCH_LINE), nl=False)
        # all but the final section have nl=False to print on same line
        for text, color in sections[:-1]:
            click.echo(click.style(text, fg=color), nl=False)
        # final section does not include nl=False
        click.echo(click.style(sections[-1][0], fg=sections[-1][1]))


class Search:
    """Master search instance. Typical use is to instantiate an instance and
    set what to search for and which file types to search, then call the
    search_folder method one or more times to do the searches, then call the
    print_summary method to print a summary.
    """

    def __init__(self, search_for: str, file_types: List[str]) -> None:
        """Constructor

        Args:
            search_for: text to be searched for
            file_types: list of file types to search, with preceding period
                on each (e.g., [".py", ".ipynb"])

        Returns:
            None
        """
        self.search_for: str = search_for
        self.file_types: List[str] = file_types

        self.searched_folders: int = 0
        self.searched_files: int = 0
        self.searched_lines: int = 0
        self.searched_bytes: int = 0

        self.last_folder_printed = ""
        self.last_file_printed = ""

        self.console_width = get_console_width()

    def print_search_match(self, match: Match) -> None:
        """Prints a match to console.

        This is a wrapper around the Match.print_match method, to format the
        output as appropriate for printing within the context of a Search
        instance.
        """
        if self.last_folder_printed != match.file.parent:
            click.echo("\r", nl=False)  # reset console to start of line
            prefix = "folder: ".rjust(config.PREFIX_LENGTH)
            folder_name = pad_string(
                str(match.file.parent), self.console_width - config.PREFIX_LENGTH
            )

            click.echo(click.style(f"{prefix}{folder_name}", fg=config.COLOR_FOLDER))
            self.last_folder_printed = match.file.parent
            self.last_file_printed = ""

        if self.last_file_printed != match.file.name:
            prefix = " " * config.PREFIX_LENGTH
            click.echo(
                click.style(f"{prefix}{match.file.name}", fg=config.COLOR_FILENAME)
            )
            self.last_file_printed = match.file.name

        match.print_match()

    def print_summary(self):
        """Prints the search totals to the console.
        """
        click.echo("\r", nl=False)  # reset console to start of line
        prefix = "Searched: ".rjust(config.PREFIX_LENGTH)
        summary_text = (
            f"{prefix}{self.searched_folders} folders, "
            f"{self.searched_files} files, "
            f"{self.searched_lines} lines, "
            f"{self.searched_bytes} bytes"
        )
        click.echo(
            click.style(
                pad_string(summary_text, self.console_width), fg=config.COLOR_SUMMARY
            )
        )

    def reset_totals(self) -> None:
        """Resets search totals to start a new set of searches.
        """
        self.searched_folders = 0
        self.searched_files = 0
        self.searched_lines = 0
        self.searched_bytes = 0

    def search_folder(
        self, folder: str, subdirs: bool = False, print_matches: bool = True
    ) -> List[Match]:
        """Searches a folder's files.

        Args:
            folder: name of the folder to be searched
            subdirs: whether to recursively search all subfolders
            print_matches: whether to print matches to the console

        Returns:
            A list of the matches found, as Match objects
        """
        matchlist = []
        for curdir, dirs, files in os.walk(folder):
            current_folder: Path = Path(curdir)
            if (
                current_folder.name in config.SKIPPED_FOLDERS
                or current_folder.name.endswith(".egg-info")
            ):
                continue

            folder_full_line = pad_string(
                f"\r{str(current_folder)}\r", self.console_width
            )
            click.echo(
                click.style(folder_full_line, fg=config.COLOR_SEARCHED_FOLDERS),
                nl=False,
            )

            if not subdirs:
                del dirs[:]  # Don't search subfolders.
            self.searched_folders += 1
            for file in files:
                # file_to_search: Path = Path(file)
                file_to_search: Path = Path(curdir).joinpath(file)
                if file_to_search.suffix.lower() in self.file_types:
                    self.searched_files += 1
                    matches, lines_count, bytes_count = search_file(
                        file_to_search, self.search_for
                    )
                    self.searched_lines += lines_count
                    self.searched_bytes += bytes_count
                    for match in matches:
                        matchlist.append(match)
                        if print_matches:
                            self.print_search_match(match)
        return matchlist


def get_console_width() -> int:
    """Gets the current width of the console screen in characters.

    Args:
        None

    Returns:
        Current screen width in characters.
    """
    full_width, _ = shutil.get_terminal_size((80, 20))
    return full_width - 1


def highlight_match(match_line: str, match_text: str, max_chars: int) -> List[Tuple]:
    """Converts a match to a set of color-highlighted strings to be printed to
    the console.

    Args:
        match_line: the line of text where a match was found
        match_text: the text to be highlighted (i.e., what was searched for)
        max_chars: the maximum total number of characters to be returned

    Returns:
        A list of (text, color) tuples for printing with click.echo/click.style.

    Note that we only highlight the first match if there are multiple matches
    in a single line.
    """

    # toprint = the portion of the line that will be printed to the console
    toprint: str
    if match_text.lower() in match_line[:max_chars].lower():
        # The match is in the first max_chars of the line.
        toprint = match_line[:max_chars]
    elif match_text.lower() in match_line[-max_chars:].lower():
        # The match is in the last max_chars of the line.
        toprint = match_line[-max_chars:]
    else:
        # This is a very long line relative to the console, and we need to find
        # a max_chars long substring in the middle of it that contains the
        # matched text. We'll try to position the match in the center of this
        # substring.
        # match_start = starting position of the match
        match_start: int = match_line.lower().find(match_text.lower())
        # center = the position of the center of the substring
        center: int = match_start + len(match_text) // 2
        # substring_start = the start of the extracted substring
        substring_start: int = center - max_chars // 2
        toprint = match_line[substring_start : substring_start + max_chars]

    # Now we break toprint into colored sections. The matched search text will
    # be config.COLOR_MATCH_TEXT, the rest of the line is config.COLOR_MATCH_LINE.
    sections: List[Tuple] = []
    match_position: int = toprint.lower().find(match_text.lower())
    if match_position > 0:
        sections.append((toprint[:match_position], config.COLOR_MATCH_LINE))
    sections.append(
        (
            toprint[match_position : match_position + len(match_text)],
            config.COLOR_MATCH_TEXT,
        )
    )
    if match_position < len(toprint) - len(match_text):
        sections.append(
            (toprint[match_position + len(match_text) :], config.COLOR_MATCH_LINE)
        )
    return sections


def is_notebook(file: Union[Path, str]) -> bool:
    """Determines whether a file is a notebook file or not.

    Args:
        file: the file, as either a pathlib.Path object or a filename string.

    Returns:
        True if notebook file, else False.
    """
    if isinstance(file, str):
        return Path(file).suffix.lower() == ".ipynb"
    return file.suffix.lower() == ".ipynb"


def pad_string(string: str, length: int) -> str:
    """Pads a string to specified length.

    Args:
        string: the text string to be padded with spaces
        length: the length of the returned string

    Returns:
        A string exactly length characters long.

    This is a helper function to hide the messy ljust()[] syntax, which is
    needed many places in pyfind because of the re-use of a single console
    line for running status information about which folders are being searched.
    """
    return string.ljust(length)[:length]


def search_file(file: str, search_for: str) -> Tuple[List[Match], int, int]:
    """Searches a file for a specified string.

    Args:
        file: name of the file to be searched (str)
        search_for: the text to search for

    Returns:
        A tuple containing these three values:
        - a list of Match objects
        - number of lines searched
        - number of bytes searched (i.e., file size in bytes)
    """
    file_path: Path = Path(file)

    matches: List[Match] = []
    line_count: int = 0
    byte_count: int = file_path.stat().st_size

    if is_notebook(file):
        # special case for searching Jupyter notebook files
        with file_path.open(errors="replace") as notebook_file:
            notebook_data: dict = json.loads(notebook_file.read())
        cell_no: int
        cell: dict
        for cell_no, cell in enumerate(notebook_data["cells"]):
            if cell["cell_type"] == "code":
                source_line: str
                for source_line in cell["source"]:
                    line_count += 1
                    if search_for.lower() in source_line.lower():
                        matches.append(
                            Match(file_path, source_line.strip(), cell_no, search_for)
                        )
        return (matches, line_count, byte_count)

    # plain text search for all other file types
    with file_path.open(errors="replace") as searchfile:
        lineno: int
        line: str
        for lineno, line in enumerate(searchfile, 1):
            line_count += 1
            if search_for.lower() in line.lower():
                matches.append(Match(file_path, line.strip(), lineno, search_for))
    return (matches, line_count, byte_count)


def textfile_to_list(filename: str) -> List[str]:
    """Reads a text file and returns a list of its non-empty lines.

    Args:
        filename: name of the text file

    Returns:
        list of the non-empty lines.
    """
    returned_list = []
    with Path(filename).open() as fhandle:
        for line in fhandle:
            if line.strip():
                returned_list.append(line.strip())
    return returned_list
