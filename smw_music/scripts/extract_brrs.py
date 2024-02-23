#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""BRR Extraction Tool."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import argparse
import sys
from collections import defaultdict
from os import makedirs
from pathlib import Path
from typing import Callable, MutableMapping

# Package imports
from smw_music.common import __version__
from smw_music.spc700 import BLOCK_SIZE, Brr, extract_brrs

###############################################################################
# Private function definitions
###############################################################################


def _extract(
    spc: Path, shift_check: bool, filt_check: bool, loop_check: bool
) -> None:
    with open(spc, "rb") as fobj:
        data = fobj.read()

    all_brrs = extract_brrs(data)
    brrs = defaultdict(list)

    if all_brrs:
        # Filter dupes
        for n, brr in enumerate(all_brrs):
            brrs[brr].append(n)

        # If the loop point doesn't point to the start of a block, discard
        _filter(
            brrs,
            lambda brr: brr.loop_point is None
            or (brr.loop_point % BLOCK_SIZE == 0),
        )

        # Confirm that the loop point is somewhere in the sample
        if loop_check:
            _filter(
                brrs,
                lambda brr: brr.loop_point is None
                or (0 <= brr.loop_point < len(brr.binary)),
            )

        # Shift values 13-15 are not valid
        if shift_check:
            _filter(brrs, lambda brr: all(x <= 12 for x in brr.ranges))

        # Samples usually should start with a filter 0
        if filt_check:
            _filter(brrs, lambda brr: brr.filters[0] == 0)

        nbrrs = len(brrs)
        width = 1 if nbrrs < 10 else 2 if nbrrs < 100 else 3

        subdir = spc.stem + " BRRs"
        outdir = spc.parent / subdir

        makedirs(outdir, exist_ok=True)

        with open(outdir / "summary.txt", "w") as sum_fobj:
            for n, (brr, samples) in enumerate(brrs.items()):
                fname = f"{n:0{width}d}.brr"
                sum_fobj.write(f"{fname}: {samples}\n")

                with open(outdir / fname, "wb") as fobj:
                    fobj.write(brr.binary)

        print(f"Extracted {nbrrs} BRRs")
    else:
        print("Could not find any BRRs")


###############################################################################


def _filter(
    brrs: MutableMapping[Brr, list[int]], valid: Callable[[Brr], bool]
) -> None:
    for brr in list(brrs.keys()):
        if not valid(brr):
            # Shift values 13-15 are not valid
            del brrs[brr]


###############################################################################
# API function definitions
###############################################################################


def main(arg_list: list[str] | None = None) -> None:
    """BRR Extractor"""
    if arg_list is None:
        arg_list = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description=f"SMW Music BRR Extractor v{__version__}"
    )
    parser.add_argument("spc", type=Path, help="Source SPC file")
    parser.add_argument(
        "--shiftcheck",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable block shift check",
    )
    parser.add_argument(
        "--filtcheck",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable block 0 filter check",
    )
    parser.add_argument(
        "--loopcheck",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable loop-point check",
    )

    args = parser.parse_args(arg_list)

    _extract(args.spc, args.shiftcheck, args.filtcheck, args.loopcheck)


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
