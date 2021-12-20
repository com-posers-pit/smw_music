#!/usr/bin/env python3

"""Music XML -> AMK Converter."""

###############################################################################
# Standard Library imports
###############################################################################

import argparse

###############################################################################
# Package imports
###############################################################################

import smw_music.music_xml

###############################################################################
# API function definitions
###############################################################################


def main():
    parser = argparse.ArgumentParser(description="Music XML -> AMK Converter")
    parser.add_argument("music_xml", type=str, help="Source Music XML file")
    parser.add_argument("amk", type=str, help="Output AMK file")

    args = parser.parse_args()

    smw_music.music_xml.Song.from_music_xml(args.music_xml).to_amk(args.amk)


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
