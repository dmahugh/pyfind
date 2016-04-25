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
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.argument('searchfor')
@click.command(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='1.0', prog_name='PyFind')
def cli(searchfor, startdir):
    """Command-line wrapper for find() function.

    /// design command-line syntax; something like this:
    /// c:> pyfind "searchfor" startdir --subdirs --pyfind --nodisplay --filetypes=py/txt

    /// LATER: implement verbosity levels; show matches versus summarize files plus number of matches each
 
    Prints to the console all matches found.
    """
    if not startdir:
        startdir = os.getcwd()

    get_matches(searchfor=searchfor, startdir=startdir)

#------------------------------------------------------------------------------
def get_matches(*, searchfor='', startdir=os.getcwd(), subdirs=False,
                filetypes=None, pyfind=True, display=True):
    """Search text files, return list of matches.

    searchfor = string to search for (not case-sensitive)
    startdir = path to folder to be searched
    subdirs = whether to search subdirectories of dir
    filetypes = list of file types (extensions) to search; lowercase
    pyfind = whether to only search folders with a _pyfind file in them
    display = whether to display matches as they're found

    Returns a list of dictionaries with these keys: folder, filename,
    lineno, linetext.
    """
    if not searchfor or not filetypes:
        return []

    output = MatchPrinter()

    matchlist = []
    for root, dirs, files in os.walk(startdir):
        if not subdirs:
            del dirs[:] # don't search subfolders
        if pyfind and not os.path.isfile(os.path.join(root, '_pyfind')):
            continue # don't search folders that don't have _pyfind
        for file in files:
            if os.path.splitext(file)[1].lower() in filetypes:
                fullname = os.path.join(root, file)
                with open(fullname, 'r') as searchfile:
                    for lineno, line in enumerate(searchfile, 1):
                        if searchfor.lower() in line.lower():
                            match = {'folder': root, 'filename': file,
                                     'lineno': lineno, 'linetext': line}
                            matchlist.append(match)
                            if display:
                                output.display(match)

    if display:
        print_summary(matchlist)

    return matchlist

#-------------------------------------------------------------------------------
def print_summary(hitlist):
    """Print summary of search results: # of folders, files, matches.

    parameter = the list of dictionaries returned by get_matches().
    """
    folders = []
    filenames = []

    for match in hitlist:
        folder = match['folder']
        filename = match['filename']
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

        parameter = dictionary of folder, filename, lineno, linetext
        """
        folder = match_tuple['folder']
        filename = match_tuple['filename']
        lineno = match_tuple['lineno']
        linetext = match_tuple['linetext']

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
                          filetypes=['.py'], pyfind=True)
