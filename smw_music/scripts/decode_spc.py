#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

###############################################################################
# Standard Library imports
###############################################################################

import argparse
import pkgutil
import sys

###############################################################################
# Library imports
###############################################################################

from mako.template import Template  # type: ignore

###############################################################################
# Package imports
###############################################################################

from smw_music import __version__
from smw_music.spc import Spc

###############################################################################
# Private function definitions
###############################################################################


def _decode_spc_file(fname: str):
    spc_data = Spc.from_file(fname)
    tmpl = Template(  # nosec - generates a .txt output, no XSS concerns
        pkgutil.get_data("smw_music", "data/spc_output.txt")
    )
    print(tmpl.render(fname=fname, spc=spc_data))


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

    _decode_spc_file(args.spc_file)


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
