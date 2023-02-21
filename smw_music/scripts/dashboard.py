#!/usr/bin/python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Music XML -> MML Dashboard."""

###############################################################################
# Standard library imports
###############################################################################

# Standard library imports
import argparse
import logging

# Library imports
from PyQt6.QtWidgets import QApplication

# Package imports
from smw_music.ui.dashboard import Dashboard

###############################################################################
# API function definitions
###############################################################################


def main() -> None:
    parser = argparse.ArgumentParser("UI")
    parser.add_argument("-v", action="count", default=0, help="Verbosity")

    args, _ = parser.parse_known_args()
    level = {
        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
    }.get(args.v, logging.DEBUG)

    logging.basicConfig(level=level)

    logging.info("Starting application")

    app = QApplication([])
    app.setApplicationName("MusicXML -> MML")
    _ = Dashboard()
    app.exec()


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
