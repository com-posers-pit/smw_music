#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Parse and describe a BRR file."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import argparse
import sys

# Package imports
from smw_music import __version__
from smw_music.brr import Brr

###############################################################################
# Private function definitions
###############################################################################


def _describe(fname: str) -> None:
    brr = Brr.from_file(fname)
    print(f"Blocks: {brr.nblocks}")
    print(f"Loop block: {brr.loop_block}")
    csv = brr.csv.split("\n")
    print(f"Block,{csv[0]}")
    for n, block in enumerate(csv[1:]):
        print(f"{n},{block}")


###############################################################################
# API function definitions
###############################################################################


def main(arg_list: list[str] | None = None) -> None:
    """Entrypoint for BRR Tool"""
    if arg_list is None:
        arg_list = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description=f"SMW Music BRR tool v{__version__}"
    )
    parser.add_argument("brr", type=str, help="Source BRR file")

    args = parser.parse_args(arg_list)

    _describe(args.brr)


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
