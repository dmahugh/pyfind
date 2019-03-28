"""search _todo.txt files in all Dropbox projects

This is a simple standalone tool to search the _todo.txt files that I use
to track work in each project. It's probably not useful to anyone else, but
extremely useful to me.
"""
from pathlib import Path
import subprocess
import sys

def main(searchfor):
    """search _todo.txt files for specified text
    """
    for filename in get_todo_files():
        file = Path(filename)
        hits_found = False # whether a match has been found in this file
        for line in file.read_text().lower().split("\n"):
            if searchfor.lower() in line:
                if not hits_found:
                    print("\n" + filename[25:-10].ljust(80, "-"))
                    hits_found = True
                print(line)


def get_todo_files():
    """Return a list of all _todo.txt files in project folders.
    """
    folders = subprocess.getoutput(r'dir ..\..\_todo.txt /s | find "Directory of"')
    return [line.strip()[13:] + r"\_todo.txt"
            for line in folders.split("\n")
            if line.strip()]

if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("USAGE: python todo_search.py searchfor")
