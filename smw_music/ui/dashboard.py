#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard application."""

###############################################################################
# Standard Library imports
###############################################################################

from typing import Optional

###############################################################################
# Library imports
###############################################################################

from PyQt6.QtWidgets import (  # type: ignore
    QApplication,
    QMainWindow,
    QMessageBox,
    QTextEdit,
)

###############################################################################
# Package imports
###############################################################################

from .. import __version__
from ..music_xml.echo import EchoConfig
from .controller import Controller
from .model import Model

###############################################################################
# API class definitions
###############################################################################


class Dashboard(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self._model = Model()
        self._controller = Controller()
        self._edit_window = QMainWindow(parent=self)
        self._edit = QTextEdit()

        self._edit_window.setMinimumSize(800, 600)

        self._setup_menus()
        self._setup_output()
        self._attach_signals()

        self.setCentralWidget(self._controller)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _about(self) -> None:
        title = "About MusicXML -> MML"
        text = f"Version: {__version__}"
        text += "\nCopyright Ⓒ 2022 The SMW Music Python Project Authors"
        text += "\nHomepage: https://github.com/com-posers-pit/smw_music"

        QMessageBox.about(self, title, text)

    ###########################################################################

    def _attach_signals(self) -> None:
        controller = self._controller
        model = self._model

        controller.artic_changed.connect(model.update_artic)
        controller.config_changed.connect(model.set_config)
        controller.instrument_changed.connect(model.set_instrument)
        controller.mml_requested.connect(self._generate_mml)
        controller.pan_changed.connect(model.set_pan)
        controller.quicklook_opened.connect(self._edit_window.show)
        controller.song_changed.connect(model.set_song)
        controller.volume_changed.connect(model.update_dynamics)
        model.inst_config_changed.connect(controller.change_inst_config)
        model.mml_generated.connect(self._edit.setText)
        model.response_generated.connect(controller.log_response)
        model.song_changed.connect(controller.update_song)

    ###########################################################################

    def _generate_mml(self, fname: str, echo: Optional[EchoConfig]) -> None:
        if self._edit_window.isVisible() or fname:
            self._model.generate_mml(fname, echo)
        else:
            self._controller.log_response(
                True,
                "Generation Error",
                "Select an MML file or open the Quicklook",
            )

    ###########################################################################

    def _setup_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("&Load project")
        file_menu.addAction("&Save project")
        file_menu.addSeparator()
        file_menu.addAction("&Quit", QApplication.quit)

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction("About", self._about)
        help_menu.addAction("About Qt", QApplication.aboutQt)

    ###########################################################################

    def _setup_output(self) -> None:
        self._edit.setReadOnly(True)
        self._edit.setFontFamily("Courier")
        self._edit_window.setCentralWidget(self._edit)
