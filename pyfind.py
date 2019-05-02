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
    "-d",
    "--depth",
    default="*",
    help="Search depth: 0 to search specified folder only, 1 to search folder plus top-level subfolders, * to search all subfolders; default=*",
)
@click.option(
    "-af",
    "--allfolders",
    is_flag=True,
    help="Search ALL folders. If omitted, "
    + "only searches folders that have a _pyfind file.",
)
@click.option(
    "-ft",
    "--filetypes",
    metavar="<str>",
    help="File types to search. Multiple types may "
    + "be delimited with /. Default: -ft=py/ipynb",
)
@click.option(
    "-nh", "--nohits", is_flag=True, help="Don't display individual search hits."
)
@click.option("-nf", "--nofiles", is_flag=True, help="Don't display filenames/folders.")
@click.option(
    "-t",
    "--totals",
    default=True,
    is_flag=True,
    help="Don't display total folders/files/lines/bytes searched",
)
@click.version_option(version="1.1", prog_name="PyFind")
def cli(searchfor, startdir, filetypes, nohits, nofiles, totals, allfolders, depth):
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
        allfolders=allfolders,
        depth=depth,
        nohits=nohits,
        nofiles=nofiles,
    )

    if totals:
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


def get_matches(
    *,
    searchfor="",
    startdir=Path.cwd(),
    filetypes=None,
    allfolders=False,
    depth="*",
    nohits=False,
    nofiles=False
):
    """Search text files, return list of matches.

    searchfor --> string to search for (not case-sensitive)
    startdir ---> path to folder to be searched; special cases:
                  '*projects' = search our projects as defined in projects.txt
                  '*packages' = installed Python packages
                  '*stdlib' = Python standard library
    depth ------> subdir depth to search; default: * (all)
    filetypes --> list of file types (extensions) to search; lowercase
    allfolders -> whether to search all folders; if false, only folders with a
                  _pyfind file in them are searched
    nohits -----> whether to suppress output of search hits (matching lines)
    nofiles ----> whether to suppress output of filenames/folders

    Returns a list of dictionaries with these keys: folder, filename,
    location, linetext.
    """
    output = MatchPrinter()

    if not searchfor:
        return []
    if not filetypes:
        filetypes = [".py", ".ipynb"]  # default if no filetypes provided
    if startdir.lower().startswith("*project"):
        # this is a special case, which we handle here and return
        pyfind_folder = Path(os.path.realpath(__file__)).parent
        projects_file = Path.joinpath(pyfind_folder, "projects.txt")
        if not os.path.isfile(projects_file):
            click.echo(click.style(f"FILE NOT FOUND: {projects_file}", fg="red"))
            return
        matchlist = []
        with open(projects_file) as folder_list:
            for line in folder_list:
                folder = line.strip()
                if not os.path.isdir(folder):
                    click.echo(click.style(f"FOLDER NOT FOUND: {folder}", fg="red"))
                    continue
                for filename in glob(f"{folder}/*.*"):
                    if os.path.splitext(filename)[1].lower() not in filetypes:
                        continue
                    for match in search_file(os.path.basename(filename),
                                             searchfor,
                                             folder):
                        matchlist.append(match)
                        output.display(match, nohits, nofiles)
        print_summary(matchlist)
        return
    if startdir.lower().startswith("*package"):
        # special case: search installed packages source code
        startdir = site.getsitepackages()[-1]
        allfolders = True
    if startdir.lower().startswith("*stdlib"):
        # special case: search Python standard library source code
        startdir = os.path.join(sys.exec_prefix, "Lib")
        depth = "1"  # top-level subdirs only, to not search tests, etc.
        # note: depth '1' misses the source of a few modules (e.g., xml)
        allfolders = True

    matchlist = []
    for root, dirs, files in os.walk(startdir):
        if root.lower().endswith("__pycache__"):
            continue  # don't search __pycache__ folders
        root_depth = root.replace(startdir, "").count("\\")
        if "*" not in depth and root_depth == int(depth):
            del dirs[:]  # don't search subfolders of here
        if not allfolders and not os.path.isfile(os.path.join(root, "_pyfind")):
            continue  # don't search folders that don't have _pyfind
        _settings.folders_searched += 1
        for file in files:
            if os.path.splitext(file)[1].lower() in filetypes:
                _settings.files_searched += 1
                for match in search_file(file, searchfor, root):
                    matchlist.append(match)
                    output.display(match, nohits, nofiles)
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

    summary = "{0} matches / {1} files / {2} folders".format(
        len(hitlist), len(filenames), len(folders)
    )

    click.echo(click.style(summary.rjust(75), fg="green"), nl=True)


def search_file(filename, searchfor, root_dir):
    """Searches a file and returns all hits found.
    """
    fullname = os.path.join(root_dir, filename)
    _settings.bytes_searched += os.stat(fullname).st_size

    if os.path.splitext(filename)[1].lower() == ".ipynb":
        matches = []
        # special case for searching Jupyter notebook files
        with open(fullname, "r", encoding="utf-8") as notebook_file:
            notebook_data = json.loads(notebook_file.read())
        for cell_no, cell in enumerate(notebook_data["cells"]):
            if cell["cell_type"] == "code":
                for source_line in cell["source"]:
                    if searchfor.lower() in source_line.lower():
                        matches.append({
                            "folder": root_dir,
                            "filename": filename,
                            "location": "Cell " + str(cell_no),
                            "linetext": source_line.strip(),
                        })
        return matches

    # plain text search for all other file types
    matches = []
    with open(fullname, "r", errors="replace") as searchfile:
        for lineno, line in enumerate(searchfile, 1):
            _settings.lines_searched += 1
            if searchfor.lower() in line.lower():
                matches.append({
                    "folder": root_dir,
                    "filename": filename,
                    "location": str(lineno),
                    "linetext": line,
                })
    return matches


class MatchPrinter:
    """Print matches as they're found.
    """

    def __init__(self):
        self.folder = ""
        self.filename = ""

    def display(self, match_tuple, nohits, nofiles):
        """Display a search hit.

        1st parameter = dictionary of folder, filename, location, linetext
        2nd parameter = whether to suppress output of search hits
        3rd parameter = whether to suppress output of filename/foldername
        """
        folder = match_tuple["folder"]
        filename = match_tuple["filename"]
        location = match_tuple["location"]
        linetext = match_tuple["linetext"]

        if folder != self.folder and not nofiles:
            click.echo(click.style(f"  folder: {folder}", fg="bright_green"))
            self.folder = folder
            # handle special case of the same-named file being a search hit
            # in two different folders, by resetting self.filename to an impossible
            # value to force display of the filename below even if it hasn't
            # changed since the previous hit ...
            self.filename = " / "

        if filename != self.filename and not nofiles:
            click.echo(f"          {filename}")
            self.filename = filename

        if not nohits:
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
