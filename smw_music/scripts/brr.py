#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

###############################################################################
# Standard Library imports
###############################################################################

import argparse
import sys

from typing import Optional

###############################################################################
# Standard Library imports
###############################################################################

import matplotlib.pyplot as plt  # type: ignore


###############################################################################
# Package imports
###############################################################################

from smw_music import __version__
from smw_music.brr import Brr

###############################################################################
# Private function definitions
###############################################################################


def _convert(
    brr_fname: str,
    wav_fname: Optional[str] = None,
    png_fname: Optional[str] = None,
):

    brr = Brr.from_file(brr_fname)

    if wav_fname is not None:
        brr.to_wave(wav_fname)

    if png_fname is not None:
        plt.plot(brr.decoded)
        plt.savefig(png_fname)


###############################################################################
# API function definitions
###############################################################################


def main(args=None):
    """Entrypoint for BRR Tool."""
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser(description=f"BRR Tool v{__version__}")
    parser.add_argument("brr", type=str, help="BRR Filename")
    parser.add_argument("--wav", type=str, help="Output .wav file")
    parser.add_argument("--png", type=str, help="Output .png file")

    args = parser.parse_args(args)

    _convert(args.brr, args.wav, args.png)


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
