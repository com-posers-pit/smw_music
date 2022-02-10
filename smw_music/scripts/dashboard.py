#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Music XML -> AMK Converter."""


###############################################################################
# Library imports
###############################################################################

from PyQt6.QtCore import Qt
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

        self._layout = QHBoxLayout(self)

        artics = [
            "Default",
            "Accent",
            "Staccato",
            "Accent+Staccato",
        ]

        self.sliders = {}
        for artic in artics:
            slider = ArticSlider(artic, parent=self)
            self._layout.addWidget(slider)
            self.sliders[artic] = slider
        self.reset()

        self.setLayout(self._layout)

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

        self._label = QLabel(label, self)
        self._length_slider = QSlider(Qt.Orientation.Vertical, self)
        self._vol_slider = QSlider(Qt.Orientation.Vertical, self)
        self._length_display = QLabel(self)
        self._vol_display = QLabel(self)
        self._display = QLabel(self)

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
        layout = QGridLayout(self)
        layout.addWidget(self._label, 0, 0, 1, 2)
        layout.addWidget(QLabel("Length", self), 1, 0)
        layout.addWidget(QLabel("Volume", self), 1, 1)
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
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._dyn_settings = {}
        self._artic_settings = {}

        self._control_panel = _ControlPanel(self)
        self._instrument_panel = QFrame(self)
        self._instruments = QListWidget(self)
        self._tabs = QTabWidget(self)
        self._dynamics = _DynamicsPanel(self)
        self._artics = _ArticPanel(self)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Instruments", self))
        layout.addWidget(self._instruments)
        self._instrument_panel.setLayout(layout)

        self._instruments.currentItemChanged.connect(self._stash_reload)

        self._tabs.addTab(self._dynamics, "Dynamics")
        self._tabs.addTab(self._artics, "Articulations")
        self._tabs.addTab(QWidget(self), "Echo")

        layout = QHBoxLayout(self)
        layout.addWidget(self._control_panel)
        layout.addWidget(self._instrument_panel)
        layout.addWidget(self._tabs)
        self.setLayout(layout)

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
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.song = None

        self._layout = QVBoxLayout(self)

        self._musicxml_picker = _FilePicker(
            "MusicXML",
            False,
            "Input MusicXML File",
            "MusicXML (*.mxl *.musicxml)",
            self,
        )
        self._mml_picker = _FilePicker(
            "MML", True, "Output MML File", "", self
        )
        self._load = QPushButton("Load MusicXML", self)
        self._generate = QPushButton("Generate MML", self)
        self._global_legato = QCheckBox("Global Legato", self)
        self._loop_analysis = QCheckBox("Loop Analysis", self)
        self._superloop_analysis = QCheckBox("Superloop Analysis", self)
        self._measure_numbers = QCheckBox("Measure Numbers", self)
        self._custom_samples = QCheckBox("Custom Samples", self)
        self._custom_percussion = QCheckBox("Custom Percussion", self)

        self._load.clicked.connect(self._load_musicxml)
        self._generate.clicked.connect(self._generate_mml)

        self._layout.addWidget(self._musicxml_picker)
        self._layout.addWidget(self._load)
        self._layout.addWidget(self._global_legato)
        self._layout.addWidget(self._loop_analysis)
        self._layout.addWidget(self._superloop_analysis)
        self._layout.addWidget(self._measure_numbers)
        self._layout.addWidget(self._custom_samples)
        self._layout.addWidget(self._custom_percussion)
        self._layout.addWidget(self._mml_picker)
        self._layout.addWidget(self._generate)

        self.setLayout(self._layout)

    ###########################################################################
    # Private method definitions
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
            self.song = Song.from_music_xml(fname)


###############################################################################


class _DynamicsPanel(QFrame):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._layout = QHBoxLayout(self)

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

        self.sliders = {}
        for dyn in dynamics:
            slider = _VolSlider(dyn, parent=self)
            self._layout.addWidget(slider)
            self.sliders[dyn] = slider
        self.reset()

        self._interpolate = QCheckBox("Interpolate", self)
        self._layout.addWidget(self._interpolate)

        self.setLayout(self._layout)

    ###########################################################################
    # API method definitions
    ###########################################################################

    def interpolate(self) -> None:
        pppp = self.sliders["PPPP"].value
        ffff = self.sliders["FFFF"].value

        delta = (ffff - pppp) / (len(self.sliders) - 1)
        for n, dyn in enumerate(self.sliders.values()):
            dyn.update(n * delta + pppp)

    ###########################################################################

    def get_values(self) -> list[int]:
        return [x.value for x in self.sliders.values()]

    ###########################################################################

    def reset(self) -> None:
        for n, slider in enumerate(self.sliders.values()):
            slider.update(255 * (n + 0.5) / len(self.sliders.items()))

    ###########################################################################

    def set_values(self, vals: list[int]) -> None:
        for dyn, val in zip(self.sliders.values(), vals):
            dyn.update(val)


###############################################################################


class _FilePicker(QFrame):
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
        self._layout = QHBoxLayout(self)
        self._button = QPushButton(text, self)
        self._edit = QLineEdit(self)

        self._layout.addWidget(self._button)
        self._layout.addWidget(self._edit)

        self._button.clicked.connect(self._open_dialog)
        self._edit.textChanged.connect(self._update_fname)
        self.setLayout(self._layout)

    ###########################################################################
    # Private method definitions
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


###############################################################################


class _Model:
    def __init__(self) -> None:
        pass


###############################################################################


class _VolSlider(QFrame):
    def __init__(
        self, label: str, pct: float = 0, parent: QWidget = None
    ) -> None:
        super().__init__(parent)
        self._update_in_progress = False

        self._label = QLabel(label, self)
        self._slider = QSlider(Qt.Orientation.Vertical, self)
        self._display = QLabel(self)

        self._control_box = QWidget(self)
        layout = QHBoxLayout(self._control_box)
        self._control = QLineEdit(self._control_box)
        layout.addWidget(self._control)
        self._control_label = QLabel("%", self._control_box)
        layout.addWidget(self._control_label)
        self._control_box.setLayout(layout)

        self._slider.setRange(0, 255)

        validator = QDoubleValidator(0, 100, 1, self)
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
        layout = QVBoxLayout()

        layout.addWidget(self._label)
        layout.addWidget(self._slider)
        layout.addWidget(self._control_box)
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
    window = _Controller()
    window.show()
    app.exec()


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
