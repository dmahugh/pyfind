"""Command-line tool for Python source-code search.

cli() --------> Handle command-line arguments.
find() -------> Search function.
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
def find(searchfor='', dir='', subdirs=False, filetypes=['.py'],
         drmonly=True):
    """Search text files such as source code.

    dir = path to folder to be searched
    str = string to search for (not case-sensitive)
    subdirs = whether to search subdirectories of dir
    filetypes = list of file types (extensions) to search; lowercase
    drmonly = whether to only search folders with a _find.drm file in them

    Prints to the console all matches found: folder, filename, line #, line
    """
    if not searchfor or not filetypes:
        return
    if not dir:
        dir = os.getcwd()

    matches = 0 # number of matches (lines) found
    hit_files = set() # set of files that have search hits
    hit_dirs = set() # set of directories that have search hits

    for root,dirs,files in os.walk(dir):
        if not subdirs:
            del dirs[:]
        if drmonly and not os.path.isfile(os.path.join(root, '_find.drm')):
            continue # don't search folders that don't have _find.drm in them
        for file in files:
            if os.path.splitext(file)[1].lower() in filetypes:
                fullname = os.path.join(root,file)
                with open(fullname, 'r') as searchfile:
                    found = False
                    for lineno, line in enumerate(searchfile, 1):
                        if searchfor.lower() in line.lower():
                            matches += 1
                            hit_files.add(fullname)
                            hit_dirs.add(root)
                            if not found:
                                print('\n-- ' + file + ' -- ' + root)
                                found = True
                            # print the found match
                            toprint = str(lineno) + ': ' + line.strip()
                            if len(toprint) > 77:
                                toprint = toprint[:74] + '...'
                            try:
                                print(toprint[:77])
                            except UnicodeEncodeError:
                                toprint = str(lineno) + ': ' + str(line.encode('utf8'))
                                if len(toprint) > 77:
                                    toprint = toprint[:74] + '...'
                                print(toprint)

    print('\nTOTAL FOUND: {0} matches in {1} files in {2} folders'.format(
        matches, len(hit_files), len(hit_dirs)))

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    find(searchfor='import', subdirs=False, filetypes=['.py'], drmonly=False)
