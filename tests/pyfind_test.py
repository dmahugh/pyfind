"""pytest unit tests for pyfind

Very simple, just using source files for test data, etc.
"""
from pathlib import Path

import pytest

from pyfind import search_file


def test_search_file_path1():
    """function: search_file()
    Tests passing the searched filename a pathlib.Path object.
    """

    search_for = "pathlib"
    search_in = Path("testdata.py")
    search_results = search_file(search_in,
                                 search_for,
                                 Path("."))

    assert len(search_results) == 1 # one match
    assert search_results[0]["folder"] == "."
    assert search_results[0]["filename"] == search_in.name
    assert search_results[0]["location"] == "3"
    assert search_for.lower() in search_results[0]["linetext"].lower()


def test_search_file_path2():
    """function: search_file()
    Tests passing the searched filename a pathlib.Path object.
    """

    search_for = "Whatever"
    search_in = Path("testdata.txt")
    search_results = search_file(search_in,
                                 search_for,
                                 Path("."))

    assert len(search_results) == 2
    for search_result in search_results:
        assert search_result["folder"] == "."
        assert search_result["filename"] == search_in.name
        assert search_result["location"] in ["3", "4"]
        assert search_for.lower() in search_result["linetext"].lower()


def test_search_file_path3():
    """function: search_file()
    Tests calling search_file without a folder argument.
    """

    search_for = "Whatever"
    search_in = Path("testdata.txt")
    search_results = search_file(search_in,
                                 search_for)

    assert len(search_results) == 2
    for search_result in search_results:
        assert search_result["folder"] == "."
        assert search_result["filename"] == search_in.name
        assert search_result["location"] in ["3", "4"]
        assert search_for.lower() in search_result["linetext"].lower()


def test_search_file_str1():
    """function: search_file()
    Tests passing the searched filename a string.
    """

    search_for = "pathlib"
    search_in = "testdata.py"
    search_results = search_file(search_in,
                                 search_for,
                                 Path("."))

    assert len(search_results) == 1 # one match
    assert search_results[0]["folder"] == "."
    assert search_results[0]["filename"] == search_in
    assert search_results[0]["location"] == "3"
    assert search_for.lower() in search_results[0]["linetext"].lower()


def test_search_file_str2():
    """function: search_file()
    Tests passing the searched filename a string.
    """

    search_for = "Whatever"
    search_in = "testdata.txt"
    search_results = search_file(search_in,
                                 search_for,
                                 Path("."))

    assert len(search_results) == 2
    for search_result in search_results:
        assert search_result["folder"] == "."
        assert search_result["filename"] == search_in
        assert search_result["location"] in ["3", "4"]
        assert search_for.lower() in search_result["linetext"].lower()

def test_search_file_str3():
    """function: search_file()
    Tests calling search_file without a folder argument.
    """

    search_for = "Whatever"
    search_in = "testdata.txt"
    search_results = search_file(search_in,
                                 search_for)

    assert len(search_results) == 2
    for search_result in search_results:
        assert search_result["folder"] == "."
        assert search_result["filename"] == search_in
        assert search_result["location"] in ["3", "4"]
        assert search_for.lower() in search_result["linetext"].lower()

def test_search_file_notebook():
    """function: search_file()
    Tests searching a notebook (.ipynb) file.
    """

    search_for = "requests"
    search_in = Path("testdata.ipynb")
    search_results = search_file(search_in,
                                 search_for,
                                 Path("."))

    assert len(search_results) == 1 # one match
    assert search_results[0]["folder"] == "."
    assert search_results[0]["filename"] == search_in.name
    assert search_results[0]["location"] == "Cell 1"
    assert search_for.lower() in search_results[0]["linetext"].lower()


if __name__ == "__main__":
    pytest.main()  # run all tests
