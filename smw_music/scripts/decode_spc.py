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

###############################################################################
# Package imports
###############################################################################

from smw_music import __version__
from smw_music.spc import Spc

###############################################################################
# API function definitions
###############################################################################


def main(args=None):
    """Entrypoint for SPC Parser."""
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser(description=f"SPC Parser v{__version__}")
    parser.add_argument("spc_file", type=str, help="SPC File")

    args = parser.parse_args(args)

    print(Spc.from_file(args.spc_file))


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
