#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Music XML -> AMK Converter."""


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
    QMessageBox,
    QPushButton,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

###############################################################################
# Project imports
###############################################################################

from ..music_xml.instrument import InstrumentConfig
from ..music_xml.song import Song
from ..music_xml import MusicXmlException

###############################################################################
# Private Class Definitions
###############################################################################


class _ArticPanel(QFrame):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        artics = [
            "Default",
            "Accent",
            "Staccato",
            "Accent+Staccato",
        ]

        self.sliders = {}
        for artic in artics:
            slider = ArticSlider(artic)
            self.sliders[artic] = slider

        self.reset()

        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    def get_values(self) -> list[int]:
        return [x.value for x in self.sliders.values()]

    ###########################################################################

    def reset(self) -> None:
        self.sliders["Default"].update(0x7A)
        self.sliders["Accent"].update(0x7F)
        self.sliders["Staccato"].update(0x5A)
        self.sliders["Accent+Staccato"].update(0x5F)

    ###########################################################################

    def set_values(self, vals: list[int]) -> None:
        for artic, val in zip(self.sliders.values(), vals):
            artic.update(val)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _do_layout(self) -> None:
        layout = QHBoxLayout()
        for slider in self.sliders.values():
            layout.addWidget(slider)
        self.reset()
        self.setLayout(layout)


###############################################################################


class ArticSlider(QFrame):
    def __init__(
        self,
        label: str,
        length: int = 7,
        vol: int = 15,
        parent: QWidget = None,
    ) -> None:
        super().__init__(parent)
        self._update_in_progress = False
        self._label = label

        self._length_slider = QSlider(Qt.Orientation.Vertical)
        self._vol_slider = QSlider(Qt.Orientation.Vertical)
        self._length_display = QLabel()
        self._vol_display = QLabel()
        self._display = QLabel()

        self._length_slider.setRange(0, 7)
        self._vol_slider.setRange(0, 15)

        self._attach_signals()

        self._length_slider.setValue(length)
        self._vol_slider.setValue(vol)

        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    def update(self, val: int) -> None:
        self._length_slider.setValue(val >> 4)
        self._vol_slider.setValue(val & 0xF)

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def value(self) -> int:
        length = self._length_slider.value()
        vol = self._vol_slider.value() & 0xF

        return (length << 4) | vol

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _attach_signals(self) -> None:
        self._length_slider.valueChanged.connect(self._slider_updated)
        self._vol_slider.valueChanged.connect(self._slider_updated)

    ###########################################################################

    def _do_layout(self) -> None:
        layout = QGridLayout()
        layout.addWidget(QLabel(self._label), 0, 0, 1, 2)
        layout.addWidget(QLabel("Length"), 1, 0)
        layout.addWidget(QLabel("Volume"), 1, 1)
        layout.addWidget(self._length_slider, 2, 0)
        layout.addWidget(self._vol_slider, 2, 1)
        layout.addWidget(self._length_display, 3, 0)
        layout.addWidget(self._vol_display, 3, 1)
        layout.addWidget(self._display, 4, 0, 1, 2)

        self.setLayout(layout)

    ###########################################################################

    def _slider_updated(self, _: int) -> None:
        self._length_display.setText(f"{self._length_slider.value():01X}")
        self._vol_display.setText(f"{self._vol_slider.value():02X}")
        self._display.setText(f"x{self.value:02X}")


###############################################################################


class _Controller(QFrame):
    def __init__(self, model: "_Model", parent: QWidget = None) -> None:
        super().__init__(parent)
        self._model = model

        self._dyn_settings = {}
        self._artic_settings = {}

        self._control_panel = _ControlPanel(model)
        self._instruments = QListWidget()
        self._dynamics = _DynamicsPanel()
        self._artics = _ArticPanel()

        self._instruments.currentItemChanged.connect(self._stash_reload)

        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    def update_instruments(self, instruments: list[InstrumentConfig]) -> None:
        self._instruments.clear()
        self._dyn_settings.clear()
        self._artic_settings.clear()
        for instrument in instruments:
            name = instrument.name
            self._dyn_settings[name] = instrument.dynamics
            self._artic_settings[name] = instrument.quant

            self._instruments.addItem(instrument.name)
        self._instruments.setCurrentRow(0)

    ###########################################################################
    # Private method definitions
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

    def _stash_reload(
        self, curr: QListWidgetItem, prev: QListWidgetItem
    ) -> None:
        for settings, control in [
            (self._dyn_settings, self._dynamics),
            (self._artic_settings, self._artics),
        ]:

            if prev is not None:
                settings[prev.text()] = control.get_values()

            if curr is not None:
                try:
                    control.set_values(settings[curr.text()])
                except KeyError:
                    control.reset()


###############################################################################


class _ControlPanel(QFrame):
    song_changed = pyqtSignal(Song)

    ###########################################################################

    def __init__(self, model: "_Model", parent: QWidget = None) -> None:
        super().__init__(parent)
        self._model = model

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

        self._musicxml_picker.file_changed.connect(self._load_musicxml)
        self._generate.clicked.connect(self._generate_mml)

        self._do_layout()

    ###########################################################################
    # Private method definitions
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

        self.setLayout(layout)

    ###########################################################################

    def _generate_mml(self) -> None:
        if self.song is None:
            QMessageBox.critical(self, "", "Please load a song")
        elif not self._mml_picker.fname:
            QMessageBox.critical(self, "", "Please pick an MML output file")
        else:
            try:
                self.song.to_mml_file(
                    self._mml_picker.fname,
                    self._global_legato.isChecked(),
                    self._loop_analysis.isChecked(),
                    self._superloop_analysis.isChecked(),
                    self._measure_numbers.isChecked(),
                    True,
                    False,
                    self._custom_samples.isChecked(),
                    self._custom_percussion.isChecked(),
                )
            except MusicXmlException as e:
                QMessageBox.critical(self, "Conversion Error", str(e))

    ###########################################################################

    def _load_musicxml(self) -> None:
        fname = self._musicxml_picker.fname
        if fname:
            try:
                self._model.set_song(fname)
                self.song_changed.emit(self.song)
            except Exception as e:
                QMessageBox.critical(self, "Load Error", str(e))


###############################################################################


class _DynamicsPanel(QFrame):
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
        self.reset()

        self._interpolate = QCheckBox("Interpolate")

        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    def interpolate(self) -> None:
        pppp = self._sliders["PPPP"].value
        ffff = self._sliders["FFFF"].value

        delta = (ffff - pppp) / (len(self._sliders) - 1)
        for n, dyn in enumerate(self._sliders.values()):
            dyn.update(n * delta + pppp)

    ###########################################################################

    def get_values(self) -> list[int]:
        return [x.value for x in self._sliders.values()]

    ###########################################################################

    def reset(self) -> None:
        for n, slider in enumerate(self._sliders.values()):
            slider.update(255 * (n + 0.5) / len(self._sliders.items()))

    ###########################################################################

    def set_values(self, vals: list[int]) -> None:
        for dyn, val in zip(self._sliders.values(), vals):
            dyn.update(val)

    ###########################################################################
    # Private method definitions
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

        self._button.clicked.connect(self._open_dialog)
        self._edit.textChanged.connect(self._update_fname)

        self._do_layout()

    ###########################################################################
    # Private method definitions
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

    ###########################################################################
    # API method definitions
    ###########################################################################

    def set_song(self, fname: str) -> None:
        self.song = Song.from_music_xml(fname)

    ###########################################################################

    def update_artic(self, inst: str, artic: str, val: int) -> None:
        try:
            self.song.instruments[inst].quant[artic] = val
            self.song_updated.emit(self.song)
        except KeyError:
            pass

    ###########################################################################

    def update_dynamics(self, inst: str, dyn: str, val: int) -> None:
        try:
            self.song.instruments[inst].dynamics[dyn] = val
            self.song_updated.emit(self.song)
        except KeyError:
            pass


###############################################################################


class _VolSlider(QFrame):
    def __init__(
        self, label: str, pct: float = 0, parent: QWidget = None
    ) -> None:
        super().__init__(parent)
        self._update_in_progress = False

        self._label = label
        self._slider = QSlider(Qt.Orientation.Vertical)
        self._display = QLabel()

        self._control_box = QWidget()
        layout = QHBoxLayout(self._control_box)
        self._control = QLineEdit(self._control_box)
        layout.addWidget(self._control)
        self._control_label = QLabel("%", self._control_box)
        layout.addWidget(self._control_label)
        self._control_box.setLayout(layout)

        self._slider.setRange(0, 255)

        validator = QDoubleValidator(0, 100, 1)
        self._control.setValidator(validator)

        self._attach_signals()

        self._slider.setValue(int(255 * pct / 100))

        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    def update(
        self, val: float, slider: bool = True, control: bool = True
    ) -> None:
        if self._update_in_progress:
            return

        self._update_in_progress = True
        val = int(val)
        if slider:
            self._slider.setValue(val)
        if control:
            self._control.setText(f"{100 * val / 255:5.1f}")
        self._display.setText(f"x{val:02X}")

        self._update_in_progress = False

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def value(self) -> int:
        return self._slider.value()

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _attach_signals(self) -> None:
        self._slider.valueChanged.connect(self._slider_updated)
        self._control.editingFinished.connect(self._control_updated)

    ###########################################################################

    def _control_updated(self) -> None:
        text = self._control.text()
        val = int(255 * float(text) / 100)
        self.update(val, True, False)

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

    def _slider_updated(self, val: int) -> None:
        self.update(val, False, True)


###############################################################################
# API function definitions
###############################################################################


def main():
    app = QApplication([])
    app.setApplicationName("MusicXML -> MML")
    model = _Model()
    window = _Controller(model)
    window.show()
    app.exec()


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
