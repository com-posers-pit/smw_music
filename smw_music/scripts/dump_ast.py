#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Display a parsed MusicXML AST."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import argparse
import sys

# Package imports
from smw_music import __version__
from smw_music.music_xml.song import Song

###############################################################################
# Private function definitions
###############################################################################


def _print_ast(song: Song, channel_num: int | None) -> None:
    for n, channel in enumerate(song.channels):
        if n == channel_num or channel_num is None:
            print(f"Channel {n}")
            for token in channel.tokens:
                print(f"  {token}")


###############################################################################
# API function definitions
###############################################################################


def main(arg_list: list[str] | None = None) -> None:
    """Entrypoint for MusicXML AST printer"""
    if arg_list is None:
        arg_list = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description=f"SMW Music MusicXML AST printer v{__version__}"
    )
    parser.add_argument("music_xml", type=str, help="Source Music XML file")
    parser.add_argument(
        "--channel", type=int, help="Channel number", default=None
    )

    args = parser.parse_args(arg_list)

    song = Song.from_music_xml(args.music_xml)

    _print_ast(song, args.channel)


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
