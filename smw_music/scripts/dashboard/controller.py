# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard Controller."""

###############################################################################
# Library imports
###############################################################################

from PyQt6.QtCore import pyqtSignal  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

###############################################################################
# Package imports
###############################################################################

from ...log import info, debug
from ...music_xml.instrument import InstrumentConfig
from ...music_xml.song import Song
from .panels import ArticPanel, ControlPanel, DynamicsPanel

###############################################################################
# API Class Definitions
###############################################################################


class Controller(QWidget):
    config_changed: pyqtSignal = pyqtSignal(bool, bool, bool, bool, bool, bool)
    instrument_changed: pyqtSignal = pyqtSignal(str, arguments=["inst_name"])
    inst_params_updated: pyqtSignal = pyqtSignal(str, str, int)
    mml_requested: pyqtSignal = pyqtSignal(str, arguments=["fname"])
    song_changed: pyqtSignal = pyqtSignal(str, arguments=["fname"])
    volume_changed: pyqtSignal = pyqtSignal(str, int)

    ###########################################################################

    @debug()
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._control_panel = ControlPanel()
        self._instruments = QListWidget()
        self._dynamics = DynamicsPanel()
        self._artics = ArticPanel()

        self._attach_signals()

        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    @info(True)
    def change_inst_config(self, config: InstrumentConfig) -> None:
        self._dynamics.update(config.dynamics)
        self._artics.update(config.quant)

    ###########################################################################

    @info()
    def log_response(self, error: bool, title: str, results: str) -> None:
        if error:
            QMessageBox.critical(self, title, results)
        else:
            QMessageBox.information(self, title, results)

    ###########################################################################

    @info()
    def update_song(self, song: Song) -> None:
        self._update_instruments(song.instruments)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @debug()
    def _attach_signals(self) -> None:
        self._control_panel.song_changed.connect(self.song_changed)
        self._control_panel.mml_requested.connect(self.mml_requested)
        self._control_panel.config_changed.connect(self.config_changed)

        self._instruments.currentTextChanged.connect(self.instrument_changed)
        self._dynamics.volume_changed.connect(self.volume_changed)

    ###########################################################################

    @debug()
    def _do_layout(self) -> None:
        inst_panel = QWidget()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Instruments"))
        layout.addWidget(self._instruments)
        inst_panel.setLayout(layout)

        tabs = QTabWidget()
        tabs.addTab(self._dynamics, "Dynamics")
        tabs.addTab(self._artics, "Articulations")
        tabs.addTab(QWidget(), "Echo")

        layout = QHBoxLayout()
        layout.addWidget(self._control_panel)
        layout.addWidget(inst_panel)
        layout.addWidget(tabs)
        self.setLayout(layout)

    ###########################################################################

    @debug()
    def _update_instruments(self, instruments: list[InstrumentConfig]) -> None:
        self._instruments.clear()
        for instrument in instruments:
            name = instrument.name
            # self._dyn_settings[name] = instrument.dynamics
            # self._artic_settings[name] = instrument.quant

            self._instruments.addItem(instrument.name)
        self._instruments.setCurrentRow(0)
