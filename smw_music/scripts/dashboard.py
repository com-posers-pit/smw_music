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
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

###############################################################################


class DynamicsPanel(QFrame):
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
        for n, dyn in enumerate(dynamics):
            slider = VolSlider(dyn, parent=self)
            self._layout.addWidget(slider)
            self.sliders[dyn] = slider
        self.reset()

        self._interpolate = QPushButton("Interpolate", self)
        self._interpolate.clicked.connect(self.interpolate)
        self._layout.addWidget(self._interpolate)

        self.setLayout(self._layout)

    ###########################################################################

    def reset(self) -> None:
        for n, slider in enumerate(self.sliders.values()):
            slider.update(255 * (n + 0.5) / len(self.sliders.items()))

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

    def set_values(self, vals: list[int]) -> None:
        for dyn, val in zip(self.sliders.values(), vals):
            dyn.update(val)


###############################################################################


class ArticPanel(QFrame):
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

    def reset(self) -> None:
        self.sliders["Default"].update(0x7A)
        self.sliders["Accent"].update(0x7F)
        self.sliders["Staccato"].update(0x5A)
        self.sliders["Accent+Staccato"].update(0x5F)

    ###########################################################################

    def get_values(self) -> list[int]:
        return [x.value for x in self.sliders.values()]

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

    ###########################################################################

    def update(self, val: int) -> None:
        self._length_slider.setValue(val >> 4)
        self._vol_slider.setValue(val & 0xF)

    ###########################################################################

    @property
    def value(self) -> int:
        length = self._length_slider.value()
        vol = self._vol_slider.value() & 0xF

        return (length << 4) | vol


###############################################################################


class VolSlider(QFrame):
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

    def _attach_signals(self) -> None:
        self._slider.valueChanged.connect(self._slider_updated)
        self._control.editingFinished.connect(self._control_updated)

    ###########################################################################

    def _do_layout(self) -> None:
        layout = QVBoxLayout()

        layout.addWidget(self._label)
        layout.addWidget(self._slider)
        layout.addWidget(self._control_box)
        layout.addWidget(self._display)

        self.setLayout(layout)

    ###########################################################################

    def _control_updated(self) -> None:
        text = self._control.text()
        val = int(255 * float(text) / 100)
        self.update(val, True, False)

    ###########################################################################

    def _slider_updated(self, val: int) -> None:
        self.update(val, False, True)

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

    @property
    def value(self) -> int:
        return self._slider.value()


###############################################################################


class Controller(QFrame):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._dyn_settings = {}
        self._artic_settings = {}
        layout = QHBoxLayout(self)

        list_widget = QListWidget(self)
        self._tabs = QTabWidget(self)
        self._dynamics = DynamicsPanel(self)
        self._artics = ArticPanel(self)

        list_widget.addItem("Flute")
        list_widget.addItem("Piano")
        list_widget.addItem("Guitar")
        list_widget.setCurrentRow(0)
        list_widget.currentItemChanged.connect(self.stash_reload)

        self._tabs.addTab(self._dynamics, "Dynamics")
        self._tabs.addTab(self._artics, "Articulations")

        layout.addWidget(list_widget)
        layout.addWidget(self._tabs)

        self.setLayout(layout)

    ###########################################################################

    def stash_reload(self, curr, prev) -> None:
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
# API function definitions
###############################################################################


def main():
    app = QApplication([])
    window = Controller()
    window.show()
    app.exec()


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
