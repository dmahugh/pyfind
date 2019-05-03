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


class _settings:
    """This class exists to provide a namespace used for global settings.
    """

    folders_searched = 0
    files_searched = 0
    lines_searched = 0
    bytes_searched = 0


def get_matches(*, searchfor="", startdir=Path.cwd(), filetypes=None, subfolders=False):
    """Search text files, return list of matches.

    searchfor --> string to search for (not case-sensitive)
    startdir ---> path to folder to be searched; special cases:
                  '*projects' = search projects listed in projects.txt
                  '*packages' = installed Python packages
                  '*stdlib' = Python standard library
    subfolders -> whether to search subfolders
    filetypes --> list of file types (extensions) to search; lowercase
    """
    if not searchfor:
        return
    if not filetypes:
        filetypes = [".py", ".ipynb"]  # default if no filetypes provided

    output = MatchPrinter()

    if startdir.lower().startswith("*project"):
        # this is a special case, which we handle here and return
        pyfind_folder = Path(__file__).resolve().parent
        projects_file = Path.joinpath(pyfind_folder, "projects.txt")
        if not projects_file.is_file():
            click.echo(click.style(f"FILE NOT FOUND: {projects_file}", fg="red"))
            return
        matchlist = []
        for line in projects_file.read_text().splitlines():
            folder = line.strip()
            if not Path(folder).is_dir():
                click.echo(click.style(f"FOLDER NOT FOUND: {folder}", fg="red"))
                continue
            _settings.folders_searched += 1
            for filename in glob(f"{folder}/*.*"):
                file_to_search = Path(filename)
                if file_to_search.suffix not in filetypes:
                    continue
                _settings.files_searched += 1
                for match in search_file(file_to_search.name, searchfor, folder):
                    matchlist.append(match)
                    output.display(match)

        print_summary(matchlist)
        return

    if startdir.lower().startswith("*package"):
        # special case: search installed packages source code
        search_root = Path(site.getsitepackages()[-1])
    elif startdir.lower().startswith("*stdlib"):
        # special case: search Python standard library source code
        search_root = Path(sys.exec_prefix).joinpath("Lib")
    else:
        # explicit search folder specified on command line
        search_root = Path(startdir)

    matchlist = []
    for root, dirs, files in os.walk(search_root):
        if root.lower().endswith("__pycache__"):
            continue  # don't search __pycache__ folders
        if not subfolders:
            del dirs[:]  # don't search subfolders of here
        _settings.folders_searched += 1
        for file in files:
            if Path(file).suffix.lower() in filetypes:
                _settings.files_searched += 1
                for match in search_file(file, searchfor, root):
                    matchlist.append(match)
                    output.display(match)
    print_summary(matchlist)


def print_summary(hitlist):
    """Print summary of search results: # of folders, files, matches.

    parameter = a list of matches. Each match is a dictionary with keys
                folder, filename, location, linetext.
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


def search_file(filename, searchfor, root_dir):
    """Searches a file and returns all hits found.
    """
    fullname = str(Path(root_dir).joinpath(filename))
    _settings.bytes_searched += Path(fullname).stat().st_size

    if Path(filename).suffix.lower() == ".ipynb":
        matches = []
        # special case for searching Jupyter notebook files
        with open(fullname, "r", encoding="utf-8") as notebook_file:
            notebook_data = json.loads(notebook_file.read())
        for cell_no, cell in enumerate(notebook_data["cells"]):
            if cell["cell_type"] == "code":
                for source_line in cell["source"]:
                    if searchfor.lower() in source_line.lower():
                        matches.append(
                            {
                                "folder": root_dir,
                                "filename": filename,
                                "location": "Cell " + str(cell_no),
                                "linetext": source_line.strip(),
                            }
                        )
        return matches

    # plain text search for all other file types
    matches = []
    with open(fullname, "r", errors="replace") as searchfile:
        for lineno, line in enumerate(searchfile, 1):
            _settings.lines_searched += 1
            if searchfor.lower() in line.lower():
                matches.append(
                    {
                        "folder": root_dir,
                        "filename": filename,
                        "location": str(lineno),
                        "linetext": line,
                    }
                )
    return matches


class MatchPrinter:
    """Print matches as they're found.
    """

    def __init__(self):
        self.folder = ""
        self.filename = ""

    def display(self, match_tuple):
        """Display a search hit.

        1st parameter = dictionary of folder, filename, location, linetext
        """
        folder = match_tuple["folder"]
        filename = match_tuple["filename"]
        location = match_tuple["location"]
        linetext = match_tuple["linetext"]

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


# code for standalone execution
if __name__ == "__main__":
    print("__main__()")
