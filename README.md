# pyfind
Python source-code search command-line tool

This is a tool for searching Python source code across multiple projects or packages. I use it when I'm writing code to accomplish some task and want to quickly see examples of how I've accomplished that same task before.

The default behavior is to search all local project folders defined in a ```projects.txt``` file in the pyfind home folder. For example, here's a truncated screenshot of a search for use of the ```json.dumps``` method across my projects, which I might do to remind myself of its syntax:

![json.dumps example](images/example01.png)

Each project folder where a hit was found is printed in green, the source files are printed in white, and each hit is printed in cyan with its line number.

Any file type(s) can be searched, and the default is to search ```.py``` source files and ```.ipynb``` notebook files. For notebooks, search hits show the cell number instead of line number:

![notebook example](images/example02.png)

## Installation

Pyfind should work with any Python 3 version, and ituses the [Click](http://click.pocoo.org/5/) CLI library. I like to install it as editable, so that I can make changes and have them show up immediately, so I follow these steps to install:

* Clone this repo
* Install prerequisites with ```pip install -r requirements.txt```
* Install pyfind as editable: ```pip install --editable .```

After installation, create a ```projects.txt``` file in the pyfind folder that contains all of the local folders/paths you'd like to include in the default search, one on each line.

After it's installed, you can use ```pyfind``` at a command prompt. For example, to display the help screen:

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
### special cases
Pyfind supports two special cases for the _startdir_ argument that specifies the root folder to be searched:

* _*packages_ = search the source code of all installed Python packages
* _*stdlib_ = search the source code of the Python standard library

Note that these options work with the currently active virtual environment, if any.
