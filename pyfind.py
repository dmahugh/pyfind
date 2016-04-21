"""Command-line tool for Python source-code search.

cli() ------------> Handle command-line arguments.
get_matches() ----> Search text files, return list of matches.
MatchPrinter -----> Class for printing matches.
print_summary() --> Print # of folders, files, matches.
"""
import os
import sys

import click

#------------------------------------------------------------------------------
def cli():
    """Command-line wrapper for find() function.

    Handles these command-line arguments:
    1st argument = what to search for
    /// defaults to be implemented later:
    - verbosity levels; TBD; show matches versus summarize files plus number of matches each

    Prints to the console all matches found.
    """

    pass

    #/// hexprint code to be modified:
    """
    # note that sys.argv[0] is the name of the script, so we start at argv[1]
    if len(sys.argv) < 2:
        click.echo('Syntax --> hexprint filename offset nbytes (offset/nbytes are optional)')
        return

    filename = sys.argv[1]
    offset = 0 if len(sys.argv) < 3 else int(sys.argv[2])
    totbytes = 0 if len(sys.argv) < 4 else int(sys.argv[3])
    hexdump(filename=filename, offset=offset, totbytes=totbytes)
    """

#------------------------------------------------------------------------------
def get_matches(searchfor='', startdir='', subdirs=False, filetypes=None,
                drmonly=True, display=True):
    """Search text files, return list of matches.

    dir = path to folder to be searched
    str = string to search for (not case-sensitive)
    subdirs = whether to search subdirectories of dir
    filetypes = list of file types (extensions) to search; lowercase
    drmonly = whether to only search folders with a _find.drm file in them
    display = whether to display matches as they're found

    Returns a list of tuples containing four values: folder, filename,
    line number of the match, full text of the matching line.
    """
    if not searchfor or not filetypes:
        return []
    if not startdir:
        startdir = os.getcwd()

    displayer = MatchPrinter()

    matchlist = []
    for root, dirs, files in os.walk(startdir):
        if not subdirs:
            del dirs[:]
        if drmonly and not os.path.isfile(os.path.join(root, '_find.drm')):
            continue # don't search folders that don't have _find.drm in them
        for file in files:
            if os.path.splitext(file)[1].lower() in filetypes:
                fullname = os.path.join(root, file)
                with open(fullname, 'r') as searchfile:
                    for lineno, line in enumerate(searchfile, 1):
                        if searchfor.lower() in line.lower():
                            match = (root, file, lineno, line)
                            matchlist.append(match)
                            if display:
                                displayer.display(match)

    if display:
        print_summary(matchlist)

    return matchlist

#-------------------------------------------------------------------------------
def print_summary(hitlist):
    """Print summary of search results: # of folders, files, matches.

    parameter = the list of matches returned by get_matches().
    """
    folders = []
    filenames = []

    for match in hitlist:
        folder = match[0]
        filename = match[1]
        if not folder in folders:
            folders.append(folder)
        if not filename in filenames:
            filenames.append(filename)

    summary = '{0} matches / {1} files / {2} folders'.format(
        len(hitlist), len(filenames), len(folders))

    click.echo(click.style(summary.rjust(75), fg='cyan'), nl=False)

#-------------------------------------------------------------------------------
class MatchPrinter(object):
    """Print matches as they're found.
    """
    def __init__(self):
        self.folder = ''
        self.filename = ''

    def display(self, match_tuple):
        """Display a search hit.

        parameter = tuple of folder, filename, line number, line text
        """
        folder = match_tuple[0]
        filename = match_tuple[1]
        lineno = match_tuple[2]
        linetext = match_tuple[3]

        if folder != self.folder:
            click.echo(click.style('-'*abs(74-len(folder)), fg='blue'), nl=False)
            click.echo(click.style(' ' + folder, fg='cyan'))
            self.folder = folder

        if filename != self.filename:
            click.echo(filename)
            self.filename = filename

        # print the matching line
        lineno_str = str(lineno).rjust(6) + ': '
        toprint = linetext.strip()
        if len(toprint) > 67:
            toprint = toprint[:64] + '...'
        try:
            click.echo(click.style(lineno_str + toprint, fg='cyan'))
        except UnicodeEncodeError:
            toprint = str(linetext.encode('utf8'))
            if len(toprint) > 67:
                toprint = toprint[:64] + '...'
            click.echo(click.style(lineno_str + toprint, fg='cyan'))

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    HITLIST = get_matches(searchfor='import os', startdir='..', subdirs=True,
                          filetypes=['.py'], drmonly=True)
