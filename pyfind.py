"""Command-line tool for Python source-code search.
"""
from glob import glob
import json
import os
from pathlib import Path
import site
import sys

import click

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


class _settings:
    """Provides a namespace used for global settings. Used only for totals.
    """

    folders_searched = 0
    files_searched = 0
    lines_searched = 0
    bytes_searched = 0


class MatchPrinter:
    """Prints matches as they're found.
    """

    def __init__(self):
        self.folder = ""
        self.filename = ""

    def display(self, match):
        """Display a search hit.

        1st parameter = dictionary of folder, filename, location, linetext
        """
        folder = match["folder"]
        filename = match["filename"]
        location = match["location"]
        linetext = match["linetext"]

        if folder != self.folder:
            click.echo(click.style(f"  folder: {folder}", fg="bright_green"))
            self.folder = folder
            # handle special case of the same-named file being a search hit
            # in two different folders, by resetting self.filename to an impossible
            # value to force display of the filename below even if it hasn't
            # changed since the previous hit ...
            self.filename = " / "

        if filename != self.filename:
            click.echo(f"          {filename}")
            self.filename = filename

        # print the matching line
        loc_str = location.rjust(8) + ": "
        toprint = linetext.strip()[:100]
        try:
            click.echo(click.style(loc_str + toprint, fg="cyan"))
        except UnicodeEncodeError:
            toprint = str(linetext.encode("utf8"))
            if len(toprint) > 67:
                toprint = toprint[:64] + "..."
            click.echo(click.style(loc_str + toprint, fg="cyan"))


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
def cli(searchfor, startdir, filetypes, subfolders):
    """\b
    _______________         searchfor: text to search for (required)
     |___|___|___|          startdir:  folder to search, or one of the options below
       |___|___|            *projects = project folders (defined in projects.txt)
         |___|              *stdlib   = Python standard library
           |                *packages = installed packages in current environment
    """
    # Note that the Click framework uses the above docstring for the help
    # screen.

    if filetypes:
        typelist = ["." + _.lower() for _ in filetypes.split("/")]
    else:
        typelist = []

    get_matches(
        searchfor=searchfor,
        startdir=startdir,
        filetypes=typelist,
        subfolders=subfolders,
    )

    click.echo(
        "Searched: {0} folders, {1} files, {2} lines, {3} bytes".format(
            _settings.folders_searched,
            _settings.files_searched,
            _settings.lines_searched,
            _settings.bytes_searched,
        )
    )


def get_matches(*, searchfor="", startdir=Path.cwd(), filetypes=None, subfolders=False):
    """Searches files and returns a list of matches.

    Args:
        searchfor: The string to search for (not case-sensitive).
        startdir: Path to folder to be searched, or one of these special cases:
                  *projects: search projects listed in projects.txt
                  *packages: search installed Python packages
                  *stdlib: search the Python standard library
        subfolders: Whether to search subfolders.
        filetypes: A list of file types (extensions) to be search. Each entry
                   must be lowercase and include the preceding period.

    Returns:
        None
    """
    if not searchfor:
        return
    if not filetypes:
        filetypes = [".py", ".ipynb"]  # default if no filetypes provided

    output = MatchPrinter()

    if startdir.lower().startswith("*project"):
        search_projects(searchfor, filetypes, output)
        return

    if startdir.lower().startswith("*package"):
        # special case: search installed packages source code
        search_root = Path(site.getsitepackages()[-1])
    elif startdir.lower().startswith("*stdlib"):
        # special case: search Python standard library source code
        search_root = Path(sys.exec_prefix).joinpath("Lib")
    else:
        # An explicit search folder was specified on the command line.
        search_root = Path(startdir)

    matchlist = []
    for curdir, dirs, files in os.walk(search_root):
        current_folder = Path(curdir)
        if current_folder.name == "__pycache__":
            continue  # Don't search __pycache__ folders.
        if not subfolders:
            del dirs[:]  # Don't search subfolders.
        _settings.folders_searched += 1
        for file in files:
            file_to_search = Path(file)
            if file_to_search.suffix.lower() in filetypes:
                _settings.files_searched += 1
                for match in search_file(file_to_search, searchfor, current_folder):
                    matchlist.append(match)
                    output.display(match)

    print_summary(matchlist)


def print_summary(hitlist):
    """Prints a summary of search results.

    Args:
        hitlist: A list of the matches found. Each match is a dictionary with
                 these keys: folder, filename, location, linetext

    Returns:
        None. Uses click.echo to print a summary to the console.
    """
    folders = []
    filenames = []

    for match in hitlist:
        folder = match["folder"]
        filename = match["filename"]
        if not folder in folders:
            folders.append(folder)
        if not filename in filenames:
            filenames.append(filename)

    summary = (
        f"{len(hitlist)} matches / {len(filenames)} files / {len(folders)} folders"
    )

    click.echo(click.style(summary.rjust(75), fg="green"), nl=True)


def search_file(file, searchfor, folder=Path(".")):
    """Searches a file and returns all hits found.

    Args:
        file: File to be searched. May be either a pathlib.Path object, or a
              base filename (no folder/path) passed as a string.
        searchfor: The string to search for.
        folder: The folder where the file is located, as a pathlib.Path.
            The folder argument is optional; defaults to Path(".") if omitted.

    Returns:
        A list of the matches found. Each match is a dictionary with these
        keys: folder, filename, location, linetext
    """

    if isinstance(file, str):
        # If filename was passed as a string, convert to a path.
        file = Path(file)
    fullname = folder.joinpath(file)

    _settings.bytes_searched += fullname.stat().st_size

    if file.suffix.lower() == ".ipynb":
        matches = []
        # special case for searching Jupyter notebook files
        with fullname.open(errors="replace") as notebook_file:
            notebook_data = json.loads(notebook_file.read())
        for cell_no, cell in enumerate(notebook_data["cells"]):
            if cell["cell_type"] == "code":
                for source_line in cell["source"]:
                    if searchfor.lower() in source_line.lower():
                        matches.append(
                            {
                                "folder": str(folder),
                                "filename": str(file),
                                "location": "Cell " + str(cell_no),
                                "linetext": source_line.strip(),
                            }
                        )
        return matches

    # plain text search for all other file types
    matches = []
    with fullname.open(errors="replace") as searchfile:
        for lineno, line in enumerate(searchfile, 1):
            _settings.lines_searched += 1
            if searchfor.lower() in line.lower():
                matches.append(
                    {
                        "folder": str(folder),
                        "filename": str(file),
                        "location": str(lineno),
                        "linetext": line,
                    }
                )
    return matches


def search_projects(search_for, file_types, match_printer):
    """Searches a list of project folders and displays matches found.

    Args:
        search_for: The text to search for.
        file_types: The list of file types to search (e.g., [".py", ".ipynb"]).
        match_printer: A MatchPrinter instance to use for printing the
            found matches to the console.

    Returns:
        None. Matches are printed to the console.
    """
    pyfind_folder = Path(__file__).resolve().parent
    projects_file = Path.joinpath(pyfind_folder, "projects.txt")
    if not projects_file.is_file():
        click.echo(click.style(f"FILE NOT FOUND: {projects_file}", fg="red"))
        return
    matchlist = []
    for line in projects_file.read_text().splitlines():
        folder = Path(line.strip())
        if not folder.is_dir():
            click.echo(click.style(f"FOLDER NOT FOUND: {folder}", fg="red"))
            continue
        _settings.folders_searched += 1
        for filename in glob(str(folder.joinpath("*.*"))):
            file_to_search = Path(filename)
            if file_to_search.suffix not in file_types:
                continue
            _settings.files_searched += 1
            for match in search_file(file_to_search, search_for, folder):
                matchlist.append(match)
                match_printer.display(match)

    print_summary(matchlist)
