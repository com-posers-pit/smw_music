# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard Panels."""

###############################################################################
# Library imports
###############################################################################

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

###############################################################################
# Package imports
###############################################################################

from ...log import debug, info
from .widgets import ArticSlider, FilePicker, VolSlider

###############################################################################
# API Class Definitions
###############################################################################


class ArticPanel(QWidget):
    artic_changed: pyqtSignal = pyqtSignal(
        str, int, int, arguments=["artic", "length", "volume"]
    )
    _sliders: dict[str, ArticSlider]

    ###########################################################################

    @debug()
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        artics = [
            "Default",
            "Accent",
            "Staccato",
            "Accent+Staccato",
        ]

        self._sliders = {artic: ArticSlider(artic) for artic in artics}

        self._attach_signals()
        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    @info()
    def update_artics(self, artics: dict[str, int]) -> None:
        for artic, val in artics:
            self._sliders[artic].update(val)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @debug()
    def _attach_signals(self) -> None:
        for artic, slider in self._sliders.items():
            slider.artic_changed.connect(
                lambda length, volume, artic=artic: self.artic_changed.emit(
                    artic, length, volume
                )
            )

    ###########################################################################

    @debug()
    def _do_layout(self) -> None:
        layout = QHBoxLayout()
        for slider in self._sliders.values():
            layout.addWidget(slider)
        self.setLayout(layout)


###############################################################################


class ControlPanel(QWidget):
    config_changed = pyqtSignal(
        [bool, bool, bool, bool, bool, bool],
        arguments=[
            "global_legato",
            "loop_analysis",
            "superloop_analysis",
            "measure_numbers",
            "custom_samples",
            "custom_percussion",
        ],
    )
    mml_requested = pyqtSignal(str, arguments=["fname"])
    song_changed = pyqtSignal(str, arguments=["fname"])

    _musicxml_picker: FilePicker
    _mml_picker: FilePicker
    _generate: QPushButton
    _global_legato: QCheckBox
    _loop_analysis: QCheckBox
    _superloop_analysis: QCheckBox
    _measure_numbers: QCheckBox
    _custom_samples: QCheckBox
    _custom_percussion: QCheckBox

    ###########################################################################

    @debug()
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._musicxml_picker = FilePicker(
            "MusicXML",
            False,
            "Input MusicXML File",
            "MusicXML (*.mxl *.musicxml);;Any (*)",
            self,
        )
        self._mml_picker = FilePicker("MML", True, "Output MML File", "", self)
        self._generate = QPushButton("Generate MML")
        self._global_legato = QCheckBox("Global Legato")
        self._loop_analysis = QCheckBox("Loop Analysis")
        self._superloop_analysis = QCheckBox("Superloop Analysis")
        self._measure_numbers = QCheckBox("Measure Numbers")
        self._custom_samples = QCheckBox("Custom Samples")
        self._custom_percussion = QCheckBox("Custom Percussion")

        self._attach_signals()
        self._do_layout()

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @debug()
    def _attach_signals(self) -> None:
        self._global_legato.stateChanged.connect(self._update_config)
        self._loop_analysis.stateChanged.connect(self._update_config)
        self._superloop_analysis.stateChanged.connect(self._update_config)
        self._measure_numbers.stateChanged.connect(self._update_config)
        self._custom_samples.stateChanged.connect(self._update_config)
        self._custom_percussion.stateChanged.connect(self._update_config)

        self._musicxml_picker.file_changed.connect(self._load_musicxml)
        self._generate.clicked.connect(self._generate_mml)

    ###########################################################################

    @debug()
    def _do_layout(self) -> None:
        layout = QVBoxLayout()

        layout.addWidget(self._musicxml_picker)
        layout.addWidget(self._global_legato)
        layout.addWidget(self._loop_analysis)
        layout.addWidget(self._superloop_analysis)
        layout.addWidget(self._measure_numbers)
        layout.addWidget(self._custom_samples)
        layout.addWidget(self._custom_percussion)
        layout.addWidget(self._mml_picker)
        layout.addWidget(self._generate)
        # layout.addWidget(QPushButton("Convert"))
        # layout.addWidget(QPushButton("Playback"))

        self.setLayout(layout)

    ###########################################################################

    @debug()
    def _generate_mml(self, fname: str) -> None:
        if not fname:
            QMessageBox.critical(self, "", "Please pick an MML output file")
        else:
            self.mml_requested.emit(fname)

    ###########################################################################

    @debug()
    def _load_musicxml(self, fname: str) -> None:
        if fname:
            self.song_changed.emit(fname)

    ###########################################################################

    @debug()
    def _update_config(self, _: int) -> None:
        self.config_changed.emit(
            self._global_legato.isChecked(),
            self._loop_analysis.isChecked(),
            self._superloop_analysis.isChecked(),
            self._measure_numbers.isChecked(),
            self._custom_samples.isChecked(),
            self._custom_percussion.isChecked(),
        )


###############################################################################


class DynamicsPanel(QWidget):
    volume_changed: pyqtSignal = pyqtSignal(
        str, int, arguments=["dynamics", "vol"]
    )
    _sliders: dict[str, VolSlider]
    _interpolate: QCheckBox

    ###########################################################################

    @debug()
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        dynamics = [
            "PPPP",
            "PPP",
            "PP",
            "P",
            "MP",
            "MF",
            "F",
            "FF",
            "FFF",
            "FFFF",
        ]

        self._sliders = {}
        for dyn in dynamics:
            slider = VolSlider(dyn)
            self._sliders[dyn] = slider

        self._interpolate = QCheckBox("Interpolate")

        self._do_layout()

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @debug()
    def _attach_signals(self) -> None:
        for dyn, slider in self._sliders.items():
            slider.change_volume.connect(
                lambda x, dyn=dyn: self.volume_changed.emit(dyn, x)
            )

    ###########################################################################

    @debug()
    def _do_layout(self) -> None:
        layout = QHBoxLayout()

        for slider in self._sliders.values():
            layout.addWidget(slider)

        layout.addWidget(self._interpolate)

        self.setLayout(layout)
