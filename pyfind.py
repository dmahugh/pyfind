"""pyfind.py
Command-line tool for Python source-code search.
"""
import os
import site
import sys

import click

from dougerino import filesize

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.argument("startdir", default=".", metavar="<startdir>")
@click.argument("searchfor", metavar="searchfor")
@click.command(context_settings=CONTEXT_SETTINGS, options_metavar="<options>")
@click.option(
    "-d",
    "--depth",
    default="*",
    help="Search depth, #subdirs or *. " + "Default: -d* (all subdirs)",
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
    + "be delimited with /. Default: -ft=py",
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
@click.version_option(version="1.0", prog_name="PyFind")
def cli(searchfor, startdir, filetypes, nohits, nofiles, totals, allfolders, depth):
    """\b
    _______________
     |___|___|___|          searchfor = text to search for (required)
       |___|___|            startdir  = root folder to search from (default=current)
         |___|                          '*stdlib' = Python standard library
           |                            '*packages' = other installed packages
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
    startdir=os.getcwd(),
    filetypes=None,
    allfolders=False,
    depth="*",
    nohits=False,
    nofiles=False
):
    """Search text files, return list of matches.

    searchfor --> string to search for (not case-sensitive)
    startdir ---> path to folder to be searched; special cases:
                  '*packages' = installed Python packages
                  '*stdlib' = Python standard library
    depth ------> subdir depth to search; default: * (all)
    filetypes --> list of file types (extensions) to search; lowercase
    allfolders -> whether to search all folders; if false, only folders with a
                  _pyfind file in them are searched
    nohits -----> whether to suppress output of search hits (matching lines)
    nofiles ----> whether to suppress output of filenames/folders

    Returns a list of dictionaries with these keys: folder, filename,
    lineno, linetext.
    """
    if not searchfor:
        return []
    if not filetypes:
        filetypes = [".py"]  # default is .py if no filetypes provided
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

    output = MatchPrinter()

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
                fullname = os.path.join(root, file)
                _settings.bytes_searched += filesize(fullname)
                with open(fullname, "r", errors="replace") as searchfile:
                    for lineno, line in enumerate(searchfile, 1):
                        _settings.lines_searched += 1
                        if searchfor.lower() in line.lower():
                            match = {
                                "folder": root,
                                "filename": file,
                                "lineno": lineno,
                                "linetext": line,
                            }
                            matchlist.append(match)
                            output.display(match, nohits, nofiles)

    print_summary(matchlist)

    return matchlist


def print_summary(hitlist):
    """Print summary of search results: # of folders, files, matches.

    parameter = the list of dictionaries returned by get_matches().
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

    click.echo(click.style(summary.rjust(75), fg="cyan"), nl=True)


class MatchPrinter:
    """Print matches as they're found.
    """

    def __init__(self):
        self.folder = ""
        self.filename = ""

    def display(self, match_tuple, nohits, nofiles):
        """Display a search hit.

        1st parameter = dictionary of folder, filename, lineno, linetext
        2nd parameter = whether to suppress output of search hits
        3rd parameter = whether to suppress output of filename/foldername
        """
        folder = match_tuple["folder"]
        filename = match_tuple["filename"]
        lineno = match_tuple["lineno"]
        linetext = match_tuple["linetext"]

        if folder != self.folder and not nofiles:
            click.echo(click.style("-" * abs(107 - len(folder)), fg="blue"), nl=False)
            click.echo(folder)
            self.folder = folder
            # handle special case of the same-named file being a search hit
            # in two different folders, by resetting self.filename to an impossible
            # value to force display of the filename below even if it hasn't
            # changed since the previous hit ...
            self.filename = " / "

        if filename != self.filename and not nofiles:
            click.echo(filename)
            self.filename = filename

        if not nohits:
            # print the matching line
            lineno_str = str(lineno).rjust(6) + ": "
            toprint = linetext.strip()[:100]
            try:
                click.echo(click.style(lineno_str + toprint, fg="cyan"))
            except UnicodeEncodeError:
                toprint = str(linetext.encode("utf8"))
                if len(toprint) > 67:
                    toprint = toprint[:64] + "..."
                click.echo(click.style(lineno_str + toprint, fg="cyan"))


# code for standalone execution
if __name__ == "__main__":
    print("__main__()")
