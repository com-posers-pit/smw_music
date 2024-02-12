#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Music XML -> AMK Converter."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import argparse
import sys

# Package imports
from smw_music import __version__
from smw_music.exporters import MmlExporter
from smw_music.spcmw import Project

###############################################################################
# API function definitions
###############################################################################


def main(arg_list: list[str] | None = None) -> None:
    """Entrypoint for SPCMW command line tool."""
    if arg_list is None:
        arg_list = sys.argv[1:]
    parser = argparse.ArgumentParser(description=f"SPCMW CLI v{__version__}")
    parser.add_argument("spcmw", type=str, help="SPCMW Project File")

    args = parser.parse_args(arg_list)

    project, _ = Project.load(args.spcmw)
    MmlExporter(project).export()


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
