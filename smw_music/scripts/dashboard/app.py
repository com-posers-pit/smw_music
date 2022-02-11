#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard application."""

###############################################################################
# Library imports
###############################################################################

from PyQt6.QtWidgets import QApplication, QMainWindow

###############################################################################
# Package imports
###############################################################################

from .controller import Controller
from .model import Model

###############################################################################
# API function definitions
###############################################################################


def main():
    app = QApplication([])
    app.setApplicationName("MusicXML -> MML")
    model = Model()
    window = QMainWindow()
    controller = Controller()

    window.menuBar().addMenu("File")
    window.menuBar().addMenu("About")

    controller.mml_requested.connect(model.generate_mml)
    controller.song_changed.connect(model.set_song)
    controller.config_changed.connect(model.set_config)
    model.song_updated.connect(controller.song_updated)

    window.setCentralWidget(controller)

    window.show()
    app.exec()


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
