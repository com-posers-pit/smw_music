#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Project version bump tool."""

###############################################################################
# Standard Library imports
###############################################################################

# Standard library imports
import argparse
import glob
import re
import sys
from itertools import chain

###############################################################################
# Private function definitions
###############################################################################


def _bump_version(version):
    key = "^version = "
    _overwrite("pyproject.toml", key, f'{key}"{version}"')

    key = "__version__ = "
    _overwrite("smw_music/__init__.py", key, f'{key}"{version}"')

    key = "assert __version__ == "
    _overwrite("tests/test_smw_music.py", key, f'{key}"{version}"')

    key = "  version: "
    _overwrite("misc/mml.qml", key, f'{key}"{version}"{chr(13)}')

    key = "; beer v"
    repl = f"{key}{version}\r"
    for fname in chain(
        glob.iglob("tests/dst/*.txt"), glob.iglob("tests/dst/ui/*.mml")
    ):
        _overwrite(fname, key, repl)


###############################################################################


def _overwrite(fname: str, key: str, repl: str):
    repl = repl.lstrip("^").rstrip("$")
    with open(fname, "r+", newline="", encoding="ascii") as fobj:
        contents = fobj.readlines()
        contents = [re.sub(f"{key}.*", repl, x) for x in contents]
        fobj.seek(0)
        fobj.truncate()
        fobj.writelines(contents)


###############################################################################
# API function definitions
###############################################################################


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser("Version Update Tool")
    parser.add_argument("version", type=str, help="New Version")

    args = parser.parse_args(args)

    _bump_version(args.version)


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
