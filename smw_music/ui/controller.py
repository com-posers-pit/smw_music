# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard Controller."""

###############################################################################
# Imports
###############################################################################

# Library imports
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtWidgets import (
    QBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# Package imports
from smw_music.log import debug, info
from smw_music.music_xml.instrument import InstrumentConfig
from smw_music.music_xml.song import Song
from smw_music.ui.panels import (
    ArticPanel,
    ControlPanel,
    DynamicsPanel,
    EchoPanel,
    SamplePanel,
)
from smw_music.ui.widgets import VolSlider

###############################################################################
# API Class Definitions
###############################################################################


class Controller(QWidget):
    artic_changed = pyqtSignal(str, int)  # arguments=["artic", "quant"]
    config_changed = pyqtSignal(bool, bool, bool, bool, bool, bool)
    instrument_changed = pyqtSignal(str)  # arguments=["inst_name"])
    mml_converted = pyqtSignal()
    mml_requested = pyqtSignal(
        str,
        object,  # object type lets us pass None or an EchoConfig
    )  # arguments=[ "fname", "config", ],
    pan_changed = pyqtSignal(bool, int)  # arguments=["enable", "pan"]
    quicklook_opened = pyqtSignal()
    song_changed = pyqtSignal(str)  # arguments=["fname"]
    spc_played = pyqtSignal()
    volume_changed = pyqtSignal(
        str, int, bool
    )  # arguments=["dyn", "val", "interp"]

    _control_panel: ControlPanel
    _instruments: QListWidget
    _dynamics: DynamicsPanel
    _artics: ArticPanel
    _echo: EchoPanel
    _volume: VolSlider
    _sample: SamplePanel

    ###########################################################################

    @debug()
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._control_panel = ControlPanel()
        self._instruments = QListWidget()
        self._dynamics = DynamicsPanel()
        self._artics = ArticPanel()
        self._echo = EchoPanel()
        self._volume = VolSlider("Global Volume", hex_disp=False)
        self._sample = SamplePanel()

        self._attach_signals()

        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    @info(True)
    def change_inst_config(self, config: InstrumentConfig) -> None:
        self._dynamics.update_ui(config.dynamics, config.dynamics_present)
        self._artics.update_ui(config.quant)
        self._artics.update_pan(config.pan)

    ###########################################################################

    @debug()
    def load_insanity_samples(self, model: QStandardItemModel) -> None:
        self._sample.load_insanity_samples(model)

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
        self._volume.set_volume(song.volume)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @debug()
    def _attach_signals(self) -> None:
        self._control_panel.config_changed.connect(self.config_changed)
        self._control_panel.mml_converted.connect(self.mml_converted)
        self._control_panel.mml_requested.connect(
            lambda x: self.mml_requested.emit(x, self._echo.config)
        )
        self._control_panel.quicklook_opened.connect(self.quicklook_opened)
        self._control_panel.song_changed.connect(self.song_changed)
        self._control_panel.spc_played.connect(self.spc_played)

        self._artics.artic_changed.connect(self.artic_changed)
        self._artics.pan_changed.connect(self.pan_changed)
        self._dynamics.volume_changed.connect(self.volume_changed)
        self._instruments.currentTextChanged.connect(self.instrument_changed)

        self._volume.volume_changed.connect(
            lambda x: self.volume_changed.emit("global", x, False)
        )

    ###########################################################################

    @debug()
    def _do_layout(self) -> None:
        inst_panel = QWidget()

        layout: QBoxLayout = QVBoxLayout()
        layout.addWidget(QLabel("Instruments"))
        layout.addWidget(self._instruments)
        inst_panel.setLayout(layout)

        global_widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(self._volume)
        layout.addWidget(self._echo)
        global_widget.setLayout(layout)

        tabs = QTabWidget()
        tabs.addTab(self._dynamics, "Dynamics")
        tabs.addTab(self._artics, "Articulations/Pan")
        tabs.addTab(self._sample, "Sample")
        tabs.addTab(global_widget, "Global")

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
            self._instruments.addItem(instrument.name)

        self._instruments.setCurrentRow(0)
