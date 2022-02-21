# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard UI Widgets."""

###############################################################################
# Standard library imports
###############################################################################

from typing import Any

###############################################################################
# Library imports
###############################################################################

from PyQt6.QtCore import pyqtSignal, Qt  # type: ignore
from PyQt6.QtGui import QDoubleValidator  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QDial,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

###############################################################################
# Package imports
###############################################################################

from ..log import debug, info

###############################################################################
# Private function definitions
###############################################################################


# h/t: https://stackoverflow.com/questions/47285303
def _fix_width(edit: QLineEdit) -> None:
    font_metrics = edit.fontMetrics()
    width = font_metrics.boundingRect("1000.0").width()
    edit.setFixedWidth(width)


###############################################################################
# API Class Definitions
###############################################################################


class ArticSlider(QWidget):
    artic_changed: pyqtSignal = pyqtSignal(int, arguments=["quant"])
    _length_slider: QSlider
    _vol_slider: QSlider
    _length_display: QLabel
    _vol_display: QLabel
    _display: QLabel

    ###########################################################################

    @debug()
    def __init__(self, label: str, parent: QWidget = None) -> None:
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

    @info(True)
    def update(self, quant: int) -> None:
        length = 0x7 & (quant >> 4)
        vol = 0xF & quant

        self._length_slider.setValue(length)
        self._vol_slider.setValue(vol)
        self._length_display.setText(f"{length:X}")
        self._vol_display.setText(f"{vol:X}")
        self._display.setText(f"{quant:02X}")

        self.artic_changed.emit(quant)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @debug()
    def _attach_signals(self) -> None:
        self._length_slider.valueChanged.connect(self._update_state)
        self._vol_slider.valueChanged.connect(self._update_state)

    ###########################################################################

    @debug()
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

    @debug()
    def _update_state(self, _: int) -> None:
        length = self._length_slider.value()
        volume = self._vol_slider.value()
        quant = ((0x7 & length) << 4) | (0xF & volume)

        self.update(quant)


###############################################################################


class FilePicker(QWidget):
    file_changed = pyqtSignal(str)
    fname: str
    _save: bool
    _caption: str
    _filter: str
    _button: QPushButton
    _edit: QLineEdit

    ###########################################################################

    @debug()
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

    @debug()
    def _attach_signals(self) -> None:
        self._button.clicked.connect(self._open_dialog)
        self._edit.editingFinished.connect(self._update_fname)

    ###########################################################################

    @debug()
    def _do_layout(self) -> None:
        layout = QHBoxLayout()

        layout.addWidget(self._button)
        layout.addWidget(self._edit)

        self.setLayout(layout)

    ###########################################################################

    @debug()
    def _open_dialog(self, _: bool) -> None:
        if self._save:
            dlg = QFileDialog.getSaveFileName
        else:
            dlg = QFileDialog.getOpenFileName
        fname, _ = dlg(self, caption=self._caption, filter=self._filter)
        if fname:
            self._edit.setText(fname)
            self._update_fname()

    ###########################################################################

    @debug()
    def _update_fname(self) -> None:
        self.fname = self._edit.text()
        if self.fname:
            self.file_changed.emit(self.fname)


###############################################################################


class PanControl(QWidget):
    pan_changed: pyqtSignal = pyqtSignal(
        bool, int, arguments=["enable", "pan"]
    )
    _slider: QDial
    _display: QLabel
    _enable: QCheckBox

    ###########################################################################

    @debug()
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._slider = QDial()
        self._display = QLabel()
        self._enable = QCheckBox("Enabled")

        self._slider.setRange(0, 20)
        self._attach_signals()

        self.set_pan(False, 10)

        self._do_layout()

    ###########################################################################
    # API method definitions
    ###########################################################################

    @info(True)
    def set_pan(self, enabled: bool, pan: int) -> None:
        self._enable.setChecked(enabled)
        self._pan = pan
        if pan == 10:
            text = "C"
        elif pan < 10:
            text = f"{10*(10 - pan)}% R"
        else:
            text = f"{10*(pan - 10)}% L"
        self._display.setText(text)

        self._slider.setEnabled(enabled)
        self._display.setEnabled(enabled)
        self.pan_changed.emit(enabled, pan)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @debug()
    def _attach_signals(self) -> None:
        self._enable.stateChanged.connect(self._update_state)
        self._slider.valueChanged.connect(self._update_state)

    ###########################################################################

    @debug()
    def _do_layout(
        self,
    ) -> None:
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Pan"))
        layout.addWidget(self._slider)
        layout.addWidget(self._display)
        layout.addWidget(self._enable)

        self.setLayout(layout)

    ###########################################################################

    @debug()
    def _update_state(self, _: Any) -> None:
        enabled = self._enable.isChecked()
        self.set_pan(enabled, self._pan)

    ###########################################################################

    @property
    def _pan(self) -> int:
        return self._slider.maximum() - self._slider.value()

    ###########################################################################

    @_pan.setter
    def _pan(self, pan: int) -> None:
        pan = self._slider.maximum() - pan
        self._slider.setValue(pan)


###############################################################################


class PctSlider(QWidget):
    pct_changed: pyqtSignal = pyqtSignal(
        float, bool, arguments=["percent", "invert"]
    )
    _control: QLineEdit
    _display: QLabel
    _invert: QCheckBox
    _slider: QSlider

    ###########################################################################

    @debug()
    def __init__(self, label: str, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._slider = QSlider(Qt.Orientation.Vertical)
        self._control = QLineEdit()
        self._display = QLabel()
        self._invert = QCheckBox("Surround")

        self._attach_signals()

        self._slider.setRange(0, 1000)
        self._control.setValidator(QDoubleValidator(0, 100, 1))
        _fix_width(self._control)
        self.set_pct(0, False)

        self._do_layout(label)

    ###########################################################################
    # API method definitions
    ###########################################################################

    @info(True)
    def set_pct(self, pct: float, invert: bool) -> None:
        pct = max(0, min(100, pct))
        if invert:
            display = round(256 - 128 * pct / 100) & 0xFF
        else:
            display = round(127 * pct / 100)

        self._slider.setValue(int(10 * pct))
        self._control.setText(f"{pct:4.1f}")
        self._display.setText(f"x{display:02X}")
        self.pct_changed.emit(pct, invert)

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def state(self) -> tuple[float, bool]:
        return (float(self._control.text()), self._invert.isChecked())

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @debug()
    def _attach_signals(self) -> None:
        self._slider.valueChanged.connect(self._update_from_slider)
        self._control.editingFinished.connect(self._update_from_control)
        self._invert.clicked.connect(self._update_from_control)

    ###########################################################################

    @debug()
    def _do_layout(self, label: str) -> None:
        control_panel = QWidget()

        layout = QHBoxLayout()
        layout.addWidget(self._control)
        layout.addWidget(QLabel("%"))

        control_panel.setLayout(layout)

        layout = QVBoxLayout()

        layout.addWidget(QLabel(label))
        layout.addWidget(self._slider)
        layout.addWidget(control_panel)
        layout.addWidget(self._invert)
        layout.addWidget(self._display)

        self.setLayout(layout)

    ###########################################################################

    @debug()
    def _update_from_control(self, _: bool = False) -> None:
        try:
            pct = float(self._control.text())
        except ValueError:
            pass
        else:
            self.set_pct(pct, self._invert.isChecked())

    ###########################################################################

    @debug()
    def _update_from_slider(self, val: int) -> None:
        pct = val / 10
        self.set_pct(pct, self._invert.isChecked())


###############################################################################


class VolSlider(QWidget):
    volume_changed = pyqtSignal(int)
    _slider: QSlider
    _control: QLineEdit
    _display: QLabel
    _fmt: str

    ###########################################################################

    @debug()
    def __init__(
        self,
        label: str,
        init: int = 0,
        hex_disp: bool = True,
        parent: QWidget = None,
    ) -> None:
        super().__init__(parent)
        self._fmt = "x{:02x}" if hex_disp else "{}"
        self._slider = QSlider(Qt.Orientation.Vertical)
        self._control = QLineEdit()
        self._display = QLabel(toolTip=f"{label} hex volume value")

        self._slider.setRange(0, 255)
        self._control.setValidator(QDoubleValidator(0, 100, 1))
        _fix_width(self._control)

        self._attach_signals()

        self.set_volume(init)

        self._do_layout(label)

    ###########################################################################
    # API method definitions
    ###########################################################################

    @info(True)
    def set_volume(self, vol: int) -> None:
        self._slider.setValue(vol)
        self._control.setText(f"{100 * vol / 255:5.1f}")
        self._display.setText(self._fmt.format(vol))
        self.volume_changed.emit(vol)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    @debug()
    def _attach_signals(self) -> None:
        self._slider.valueChanged.connect(self.set_volume)
        self._control.editingFinished.connect(self._update_from_control)

    ###########################################################################

    @debug()
    def _do_layout(self, label: str) -> None:
        control_panel = QWidget()

        layout = QHBoxLayout()
        layout.addWidget(self._control)
        layout.addWidget(QLabel("%"))

        control_panel.setLayout(layout)

        layout = QVBoxLayout()

        layout.addWidget(QLabel(label))
        layout.addWidget(self._slider)
        layout.addWidget(control_panel)
        layout.addWidget(self._display)

        self.setLayout(layout)

    ###########################################################################

    @debug()
    def _update_from_control(self):
        try:
            volume = int(255 * float(self._control.text()) / 100)
        except ValueError:
            pass
        else:
            self.set_volume(volume)
