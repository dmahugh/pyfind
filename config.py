"""pyfind configuration settings
"""

# colors used for console output:
COLOR_FOLDER = "green"
COLOR_FILENAME = "white"
COLOR_MATCH_LINE = "cyan"
COLOR_MATCH_TEXT = "green"
COLOR_SUMMARY = "green"
COLOR_WARNING = "red"

# subfolders to never be searched:
SKIPPED_FOLDERS = [
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".vscode",
    "__pycache__",
    "archive",
    "backup",
    "backups",
]

# length in characters of the left column of displayed output:
PREFIX_LENGTH = 12
