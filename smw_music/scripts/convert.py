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
from smw_music.music_xml import EchoConfig, Song

###############################################################################
# API function definitions
###############################################################################


def main(arg_list: list[str] | None = None) -> None:
    """Entrypoint for Music XML -> AMK Converter."""
    if arg_list is None:
        arg_list = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description=f"Music XML -> AMK Converter v{__version__}"
    )
    parser.add_argument("music_xml", type=str, help="Source Music XML file")
    parser.add_argument("amk", type=str, help="Output AMK file")
    parser.add_argument(
        "--disable_global_legato",
        action="store_false",
        help="Disable the global legato setting",
        dest="enable_global_legato",
    )
    parser.add_argument(
        "--loop_analysis",
        action="store_true",
        help="Enable loop optimizations",
    )
    parser.add_argument(
        "--superloop_analysis",
        action="store_true",
        help="Enable superloop optimizations",
    )
    parser.add_argument(
        "--measure_numbers",
        action="store_true",
        help="Emit measure numbers",
    )
    parser.add_argument(
        "--disable_dt",
        action="store_false",
        help="Disable including datetime in MML file",
        dest="enable_dt",
    )
    parser.add_argument(
        "--echo",
        help="Echo configuration",
        type=EchoConfig.from_csv,
        default=None,
    )
    parser.add_argument(
        "--optimize_percussion",
        action="store_true",
        help="Remove repeated percussion instrument directives",
    )

    args = parser.parse_args(arg_list)

    Song.from_music_xml(args.music_xml).to_mml_file(
        args.amk,
        args.enable_global_legato,
        args.loop_analysis,
        args.superloop_analysis,
        args.measure_numbers,
        args.enable_dt,
        args.echo,
        args.optimize_percussion,
    )


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
