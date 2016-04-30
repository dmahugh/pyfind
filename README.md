# pyfind
Python source-code search command-line tool

## Installation

Pyfind uses the [Click](http://click.pocoo.org/5/) CLI library. To install for development use, clone this repo and then type this command in the repo folder:

```pip install --editable .```

That creates the *pyfind* alias to run the program, and changes to pyfind.py are immediately "live" &mdash; no need to re-install.

After it's installed, you can use the *pyfind* command to run it. For example, to display the help screen:

![help screen](https://raw.githubusercontent.com/dmahugh/pyfind/master/images/helpscreen.png)

## Usage examples

By default, pyfind searches all .py files in the current folder. For example:

![simple search](https://raw.githubusercontent.com/dmahugh/pyfind/master/images/simplesearch.png)

Note that each filename is followed by the hits within that file, and a summary at the end shows the total number of hits, files and folders. The *-nh* or *--nohits* option can be used to see a summary of the matching files only:

![nohits](https://raw.githubusercontent.com/dmahugh/pyfind/master/images/nohits.png)

To search subfolders, add the *-s* or *--subdirs* option. Hits are grouped by folder:

![subdirs](https://raw.githubusercontent.com/dmahugh/pyfind/master/images/subdirs.png)

By default, pyfind only searches .py files. Use the *-ft* or *--filetypes* option to specify other file types to be searched. You can specify multiple file types by separating the extensions with /:

![filetypes](https://raw.githubusercontent.com/dmahugh/pyfind/master/images/filetypes.png)

By default, pyfind only searches folders that contain a file named *_pyfind*. I use this option to limit searches to my own code &mdash; there's a *_pyfind* file in each folder where my code resides. You can force pyfind to search all folders with the *-af* or *--allfolders* option:

![allfolders](https://raw.githubusercontent.com/dmahugh/pyfind/master/images/allfolders.png)
