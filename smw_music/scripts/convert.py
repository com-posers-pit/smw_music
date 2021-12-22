#!/usr/bin/env python3

"""Music XML -> AMK Converter."""

###############################################################################
# Standard Library imports
###############################################################################

import argparse

###############################################################################
# Package imports
###############################################################################

from smw_music import __version__
from smw_music.music_xml import Song

###############################################################################
# API function definitions
###############################################################################


def main():
    """Entrypoint for Music XML -> AMK Converter."""
    parser = argparse.ArgumentParser(
        description=f"Music XML -> AMK Converter v{__version__}"
    )
    parser.add_argument("music_xml", type=str, help="Source Music XML file")
    parser.add_argument("amk", type=str, help="Output AMK file")

    args = parser.parse_args()

    Song.from_music_xml(args.music_xml).to_amk(args.amk)


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
