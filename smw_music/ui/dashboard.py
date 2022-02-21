#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard application."""

###############################################################################
# Library imports
###############################################################################

from PyQt6.QtWidgets import (  # type: ignore
    QApplication,
    QMainWindow,
    QMessageBox,
)

###############################################################################
# Package imports
###############################################################################

from .. import __version__
from .controller import Controller
from .model import Model

###############################################################################
# API class definitions
###############################################################################


class Dashboard(QApplication):
    def __init__(self, args: list) -> None:
        super().__init__(args)

        self.setApplicationName("MusicXML -> MML")
        self._model = Model()
        self._window = QMainWindow()
        self._controller = Controller()

        self._setup_menus()
        self._attach_signals()

        self._window.setCentralWidget(self._controller)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _about(self) -> None:
        title = "About MusicXML -> MML"
        text = f"Version: {__version__}"
        text += "\nCopyright Ⓒ 2022 The SMW Music Python Project Authors"
        text += "\nHomepage: https://github.com/com-posers-pit/smw_music"

        QMessageBox.about(self._window, title, text)

    ###########################################################################

    def _attach_signals(self) -> None:
        controller = self._controller
        model = self._model

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

    ###########################################################################

    def _setup_menus(self) -> None:
        file_menu = self._window.menuBar().addMenu("&File")
        file_menu.addAction("&Load project")
        file_menu.addAction("&Save project")
        file_menu.addSeparator()
        file_menu.addAction("&Quit", self.quit)

        help_menu = self._window.menuBar().addMenu("&Help")
        help_menu.addAction("About", self._about)
        help_menu.addAction("About Qt", self.aboutQt)

    ###########################################################################
    # API method definitions
    ###########################################################################

    def run(self) -> None:
        self._window.show()
        self.exec()
