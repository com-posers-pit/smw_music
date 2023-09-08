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
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from pathlib import Path

# Library imports
from PyQt6.QtWidgets import QApplication

# Package imports
from smw_music.ui.dashboard import Dashboard

###############################################################################
# API function definitions
###############################################################################


def main() -> None:
    """Entrypoint for Interactive GUI."""
    parser = argparse.ArgumentParser("UI")
    parser.add_argument("-v", action="count", default=0, help="Verbosity")
    parser.add_argument("project", default=None, type=Path, nargs="?")
    parser.add_argument(
        "--console", action="store_true", help="Print to console"
    )

    args, _ = parser.parse_known_args()
    level = {
        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
    }.get(args.v, logging.DEBUG)

    logging.basicConfig(level=level)

    logging.info("Starting application")

    with ExitStack() as stack:
        if not args.console:
            logfile = open("spcmw.log", "w")
            stack.enter_context(logfile)
            stack.enter_context(redirect_stdout(logfile))
            stack.enter_context(redirect_stderr(logfile))

        app = QApplication([])
        app.setApplicationName("SPaCeMusicW")
        _ = Dashboard(args.project)
        app.exec()


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
