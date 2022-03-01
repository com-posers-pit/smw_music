#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SNES Echo Filter Tool."""

###############################################################################
# Standard Library imports
###############################################################################

import argparse
import sys

###############################################################################
# Library imports
###############################################################################

import scipy.signal

import matplotlib.pyplot as plt
import numpy as np

###############################################################################
# Package imports
###############################################################################

from smw_music import __version__

###############################################################################
# Private function definitions
###############################################################################


def _decode_coeffs(arg: str) -> np.ndarray:
    coeffs = list(int(x, 0) for x in arg.split(","))

    return np.array(coeffs, dtype=np.int8)


###############################################################################
# API function definitions
###############################################################################


def main(args=None):
    """Entrypoint for Echo Filter Tool."""
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description=f"SNES Echo Filter Tool v{__version__}"
    )

    parser.add_argument("coeffs", type=_decode_coeffs)

    args = parser.parse_args(args)

    w, mag, phase = scipy.signal.dbode(
        (args.coeffs / 128, 1, 1 / (8e3)), n=1000
    )
    phase = (phase + 180) % 360 - 180
    w /= 2 * np.pi

    plt.figure()

    plt.subplot(2, 1, 1)
    plt.grid(True)
    plt.semilogx(w, mag)
    plt.ylim(-60, max(10, np.max(mag)))
    plt.xlabel("freq/Hz")
    plt.ylabel("Mag/dB")

    plt.subplot(2, 1, 2)
    plt.grid(True)
    plt.semilogx(w, phase)
    plt.ylim(-210, 210)
    plt.xlabel("freq/Hz")
    plt.ylabel("Phase/\u00b0")

    plt.show()


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
