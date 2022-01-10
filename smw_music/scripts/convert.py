#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Music XML -> AMK Converter."""

###############################################################################
# Standard Library imports
###############################################################################

import argparse
import sys

###############################################################################
# Package imports
###############################################################################

from smw_music import __version__
from smw_music.music_xml import Song

###############################################################################
# API function definitions
###############################################################################


def main(args=None):
    """Entrypoint for Music XML -> AMK Converter."""
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description=f"Music XML -> AMK Converter v{__version__}"
    )
    parser.add_argument("music_xml", type=str, help="Source Music XML file")
    parser.add_argument("amk", type=str, help="Output AMK file")
    parser.add_argument(
        "--disable_global_legato",
        action="store_true",
        help="Disable the global legato setting",
    )
    parser.add_argument(
        "--loop_analysis",
        action="store_true",
        help="Enable loop optimizations",
    )
    parser.add_argument(
        "--measure_numbers",
        action="store_true",
        help="Emit measure numbers",
    )

    args = parser.parse_args(args)

    Song.from_music_xml(args.music_xml).to_mml_file(
        args.amk,
        not args.disable_global_legato,
        args.loop_analysis,
        args.measure_numbers,
    )


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
