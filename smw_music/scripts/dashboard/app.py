#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard application."""

###############################################################################
# Standard library imports
###############################################################################

import argparse
import logging

###############################################################################
# Library imports
###############################################################################

from PyQt6.QtWidgets import QApplication, QMainWindow  # type: ignore

###############################################################################
# Package imports
###############################################################################

from .controller import Controller
from .model import Model

###############################################################################
# Private function definitions
###############################################################################


def _setup_menus(app: QApplication, window: QMainWindow) -> None:
    file_menu = window.menuBar().addMenu("&File")
    file_menu.addAction("&Load project")
    file_menu.addAction("&Save project")
    file_menu.addSeparator()
    file_menu.addAction("&Quit", app.quit)

    help_menu = window.menuBar().addMenu("&Help")
    help_menu.addAction("About")
    help_menu.addAction("About Qt", app.aboutQt)


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
    model = Model()
    window = QMainWindow()
    controller = Controller()

    _setup_menus(app, window)

    controller.artic_changed.connect(model.update_artic)
    controller.config_changed.connect(model.set_config)
    controller.instrument_changed.connect(model.set_instrument)
    controller.mml_requested.connect(model.generate_mml)
    controller.pan_changed.connect(model.set_pan)
    controller.song_changed.connect(model.set_song)
    controller.volume_changed.connect(model.update_dynamics)
    model.inst_config_changed.connect(controller.change_inst_config)
    model.response_generated.connect(controller.log_response)
    model.song_changed.connect(controller.update_song)

    window.setCentralWidget(controller)
    window.show()
    app.exec()


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
