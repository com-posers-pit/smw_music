#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Music XML -> AMK Converter."""

###############################################################################
# Standard library imports
###############################################################################

from dataclasses import dataclass

###############################################################################
# Library imports
###############################################################################

from PyQt6.QtCore import pyqtSignal, QObject, Qt
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

###############################################################################
# Package imports
###############################################################################

from ..music_xml.instrument import InstrumentConfig
from ..music_xml.song import Song

###############################################################################
# Private Class Definitions
###############################################################################


class _ArticPanel(QFrame):
    artic_changed: pyqtSignal = pyqtSignal(
        str, int, int, arguments=["artic", "length", "volume"]
    )
    _sliders: dict[str, "_ArticSlider"]

    ###########################################################################

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        artics = [
            "Default",
            "Accent",
            "Staccato",
            "Accent+Staccato",
        ]

        self._sliders = {artic: _ArticSlider(artic) for artic in artics}

        self._attach_signals()
        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    def update_artics(self, artics: dict[str, int]) -> None:
        for artic, val in artics:
            self._sliders[artic].update(val)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _attach_signals(self) -> None:
        for artic, slider in self._sliders.items():
            slider.artic_changed.connect(
                lambda length, volume, artic=artic: self.artic_changed.emit(
                    artic, length, volume
                )
            )

    ###########################################################################

    def _do_layout(self) -> None:
        layout = QHBoxLayout()
        for slider in self._sliders.values():
            layout.addWidget(slider)
        self.setLayout(layout)


###############################################################################


class _ArticSlider(QFrame):
    artic_changed: pyqtSignal = pyqtSignal(
        int, int, arguments=["length", "volume"]
    )
    _length_slider: QSlider
    _vol_slider: QSlider
    _length_display: QLabel
    _vol_display: QLabel
    _display: QLabel

    ###########################################################################

    def __init__(
        self,
        label: str,
        parent: QWidget = None,
    ) -> None:
        super().__init__(parent)

        self._length_slider: QSlider = QSlider(Qt.Orientation.Vertical)
        self._vol_slider: QSlider = QSlider(Qt.Orientation.Vertical)
        self._length_display: QLabel = QLabel()
        self._vol_display: QLabel = QLabel()
        self._display: QLabel = QLabel()

        self._length_slider.setRange(0, 7)
        self._vol_slider.setRange(0, 15)

        self._attach_signals()
        self._do_layout(label)

    ###########################################################################
    # API method definitions
    ###########################################################################

    def update(self, length: int, vol: int) -> None:
        self._length_slider.setValue(length)
        self._vol_slider.setValue(vol)
        self._length_display.setText(f"{length:X}")
        self._vol_display.setText(f"{vol:X}")
        self._display.setText(f"{length:X}{vol:X}")
        self.artic_changed.emit(length, vol)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _attach_signals(self) -> None:
        self._length_slider.valueChanged.connect(self._update_state)
        self._vol_slider.valueChanged.connect(self._update_state)

    ###########################################################################

    def _do_layout(self, label: str) -> None:
        layout = QGridLayout()

        layout.addWidget(QLabel(label), 0, 0, 1, 2)
        layout.addWidget(QLabel("Length"), 1, 0)
        layout.addWidget(QLabel("Volume"), 1, 1)
        layout.addWidget(self._length_slider, 2, 0)
        layout.addWidget(self._vol_slider, 2, 1)
        layout.addWidget(self._length_display, 3, 0)
        layout.addWidget(self._vol_display, 3, 1)
        layout.addWidget(self._display, 4, 0, 1, 2)

        self.setLayout(layout)

    ###########################################################################

    def _update_state(self, _: int) -> None:
        length = self._length_slider.value()
        volume = self._vol_slider.value()
        self.update(length, volume)


###############################################################################


class _Controller(QFrame):
    config_changed: pyqtSignal = pyqtSignal(bool, bool, bool, bool, bool, bool)
    instrument_changed: pyqtSignal = pyqtSignal(str, arguments=["inst_name"])
    inst_params_updated: pyqtSignal = pyqtSignal(str, str, int)
    mml_requested: pyqtSignal = pyqtSignal(str, arguments=["fname"])
    song_changed: pyqtSignal = pyqtSignal(str, arguments=["fname"])
    volume_changed: pyqtSignal = pyqtSignal(str, int)

    ###########################################################################

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._control_panel = _ControlPanel()
        self._instruments = QListWidget()
        self._dynamics = _DynamicsPanel()
        self._artics = _ArticPanel()

        self._attach_signals()

        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    def song_updated(self, song: Song) -> None:
        self._update_instruments(song.instruments)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _attach_signals(self) -> None:
        self._control_panel.song_changed.connect(self.song_changed)
        self._control_panel.generate_mml.connect(self.generate_mml)
        self._control_panel.update_config.connect(self.update_config)

        # self._instruments.currentItemChanged.connect(self._change_instrument)
        self._dynamics.change_volume.connect()

    ###########################################################################

    def _do_layout(self) -> None:
        inst_panel = QFrame()

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

    def _update_instruments(self, instruments: list[InstrumentConfig]) -> None:
        self._instruments.clear()
        for instrument in instruments:
            name = instrument.name
            # self._dyn_settings[name] = instrument.dynamics
            # self._artic_settings[name] = instrument.quant

            self._instruments.addItem(instrument.name)
        self._instruments.setCurrentRow(0)


###############################################################################


class _ControlPanel(QFrame):
    config_changed = pyqtSignal(str, bool, arguments=["param", "state"])
    request_mml = pyqtSignal(str, arguments=["fname"])
    song_changed = pyqtSignal(str, arguments=["fname"])
    _musicxml_picker: "_FilePicker"
    _mml_picker: "_FilePicker"
    _generate: QPushButton
    _global_legato: QCheckBox
    _loop_analysis: QCheckBox
    _superloop_analysis: QCheckBox
    _measure_numbers: QCheckBox
    _custom_samples: QCheckBox
    _custom_percussion: QCheckBox

    ###########################################################################

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._musicxml_picker = _FilePicker(
            "MusicXML",
            False,
            "Input MusicXML File",
            "MusicXML (*.mxl *.musicxml);;Any (*)",
            self,
        )
        self._mml_picker = _FilePicker(
            "MML", True, "Output MML File", "", self
        )
        self._generate = QPushButton("Generate MML")
        self._global_legato = QCheckBox("Global Legato")
        self._loop_analysis = QCheckBox("Loop Analysis")
        self._superloop_analysis = QCheckBox("Superloop Analysis")
        self._measure_numbers = QCheckBox("Measure Numbers")
        self._custom_samples = QCheckBox("Custom Samples")
        self._custom_percussion = QCheckBox("Custom Percussion")

        self._attach()
        self._do_layout()

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _attach(self) -> None:
        self._global_legato.stateChanged.connect(self._update_config)
        self._loop_analysis.stateChanged.connect(self._update_config)
        self._superloop_analysis.stateChanged.connect(self._update_config)
        self._measure_numbers.stateChanged.connect(self._update_config)
        self._custom_samples.stateChanged.connect(self._update_config)
        self._custom_percussion.stateChanged.connect(self._update_config)

        self._musicxml_picker.file_changed.connect(self._load_musicxml)
        self._generate.clicked.connect(self._generate_mml)

    ###########################################################################

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

    def _generate_mml(self) -> None:
        print("generating mml")
        if not self._mml_picker.fname:
            QMessageBox.critical(self, "", "Please pick an MML output file")
        else:
            self.request_mml.emit(self._mml_picker.fname)

    ###########################################################################

    def _load_musicxml(self) -> None:
        fname = self._musicxml_picker.fname
        if fname:
            self.song_changed.emit(fname)

    ###########################################################################

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


class _DynamicsPanel(QFrame):
    change_volume = pyqtSignal(str, int)

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
            slider = _VolSlider(dyn)
            self._sliders[dyn] = slider

        self._interpolate = QCheckBox("Interpolate")

        self._do_layout()

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _attach_signals(self) -> None:
        for dyn, slider in self._sliders.items():
            slider.change_volume.connect(
                lambda x, dyn=dyn: self.change_volume(dyn, x)
            )

    ###########################################################################

    def _do_layout(self) -> None:
        layout = QHBoxLayout()

        for slider in self._sliders.values():
            layout.addWidget(slider)

        layout.addWidget(self._interpolate)

        self.setLayout(layout)


###############################################################################


class _FilePicker(QFrame):
    file_changed = pyqtSignal(str)
    fname: str
    _save: bool
    _caption: str
    _filter: str
    _button: QPushButton
    _edit: QLineEdit

    ###########################################################################

    def __init__(
        self,
        text: str,
        save: bool,
        caption: str,
        filt: str,
        parent: QWidget = None,
    ) -> None:
        super().__init__(parent)
        self.fname = ""
        self._save = save
        self._caption = caption
        self._filter = filt
        self._button = QPushButton(text)
        self._edit = QLineEdit()

        self._attach_signals()

        self._do_layout()

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _attach_signals(self) -> None:
        self._button.clicked.connect(self._open_dialog)
        self._edit.textChanged.connect(self._update_fname)

    ###########################################################################

    def _do_layout(self) -> None:
        layout = QHBoxLayout()

        layout.addWidget(self._button)
        layout.addWidget(self._edit)

        self.setLayout(layout)

    ###########################################################################

    def _open_dialog(self) -> None:
        if not self._save:
            fname, _ = QFileDialog.getOpenFileName(
                self, caption=self._caption, filter=self._filter
            )
        else:
            fname, _ = QFileDialog.getSaveFileName(
                self, caption=self._caption, filter=self._filter
            )
        self._edit.setText(fname)

    ###########################################################################

    def _update_fname(self) -> None:
        self.fname = self._edit.text()
        self.file_changed.emit(self.fname)


###############################################################################


class _Model(QObject):
    song_updated = pyqtSignal(Song)

    ###########################################################################

    def __init__(self) -> None:
        super().__init__()
        self.song = None
        self.mml_fname = ""
        self.global_legato = False
        self.loop_analysis = False
        self.superloop_analysis = False
        self.measure_numbers = False
        self.custom_samples = False
        self.custom_percussion = False
        self.active_instrument = None

    ###########################################################################
    # API method definitions
    ###########################################################################

    def generate_mml(self, fname: str) -> None:
        self.song.to_mml_file(
            fname,
            self.global_legato,
            self.loop_analysis,
            self.superloop_analysis,
            self.measure_numbers,
            True,
            False,
            self.custom_samples,
            self.custom_percussion,
        )

    ###########################################################################

    def set_instrument(self, inst: str) -> None:
        self.active_instrument = inst

    ###########################################################################

    def set_config(
        self,
        global_legato: bool,
        loop_analysis: bool,
        superloop_analysis: bool,
        measure_numbers: bool,
        custom_samples: bool,
        custom_percussion: bool,
    ) -> None:
        self.global_legato = global_legato
        self.loop_analysis = loop_analysis
        self.superloop_analysis = superloop_analysis
        self.measure_numbers = measure_numbers
        self.custom_samples = custom_samples
        self.custom_percussion = custom_percussion

    ###########################################################################

    def set_song(self, fname: str) -> None:
        self.song = Song.from_music_xml(fname)
        self._signal()

    ###########################################################################

    def update_artic(self, inst: str, artic: str, val: int) -> None:
        try:
            self.song.instruments[inst].quant[artic] = val
            self._signal()
        except KeyError:
            pass

    ###########################################################################

    def update_dynamics(self, inst: str, dyn: str, val: int) -> None:
        try:
            self.song.instruments[inst].dynamics[dyn] = val
            self._signal()
        except KeyError:
            pass

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _signal(self) -> None:
        self.song_updated.emit(self.song)


###############################################################################


class _VolSlider(QFrame):
    volume_changed = pyqtSignal(int)
    _label: QLabel
    _slider: QSlider
    _control: QLineEdit
    _display: QLabel

    ###########################################################################

    def __init__(self, label: str, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._label = label

        self._slider = QSlider(Qt.Orientation.Vertical)
        self._control = QLineEdit()
        self._display = QLabel()

        self._slider.setRange(0, 255)
        self._control.setValidator(QDoubleValidator(0, 100, 1))

        self._attach_signals()
        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    def set_volume(self, vol: int) -> None:
        self._slider.setValue(vol)
        self._control.setText(f"{100 * vol / 255:5.1f}")
        self._display.setText(f"x{vol:02X}")

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _attach_signals(self) -> None:
        self._slider.valueChanged.connect(self._update_state)
        self._control.editingFinished.connect(
            lambda x: self._update_state(int(255 * float(x) / 100))
        )

    ###########################################################################

    def _do_layout(self) -> None:
        control_panel = QFrame()

        layout = QHBoxLayout()
        layout.addWidget(self._control)
        layout.addWidget(QLabel("%"))

        control_panel.setLayout(layout)

        layout = QVBoxLayout()

        layout.addWidget(QLabel(self._label))
        layout.addWidget(self._slider)
        layout.addWidget(control_panel)
        layout.addWidget(self._display)

        self.setLayout(layout)

    ###########################################################################

    def _update_state(self, vol: int) -> None:
        self.set_volume(vol)
        self.volume_changed.emit(vol)


###############################################################################
# API function definitions
###############################################################################


def main():
    app = QApplication([])
    app.setApplicationName("MusicXML -> MML")
    model = _Model()
    window = QMainWindow()
    controller = _Controller()

    window.menuBar().addMenu("File")
    window.menuBar().addMenu("About")

    controller.generate_mml.connect(model.generate_mml)
    controller.song_changed.connect(model.set_song)
    controller.update_config.connect(model.set_config)
    model.song_updated.connect(controller.song_updated)

    window.setCentralWidget(controller)

    window.show()
    app.exec()


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
