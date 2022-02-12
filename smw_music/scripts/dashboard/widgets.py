# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard UI Widgets."""

###############################################################################
# Library imports
###############################################################################

from PyQt6.QtCore import pyqtSignal, Qt  # type: ignore
from PyQt6.QtGui import QDoubleValidator  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
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

from ...log import debug, info

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


class VolSlider(QWidget):
    volume_changed = pyqtSignal(int)
    _slider: QSlider
    _control: QLineEdit
    _display: QLabel

    ###########################################################################

    @debug()
    def __init__(self, label: str, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._slider = QSlider(Qt.Orientation.Vertical)
        self._control = QLineEdit()
        self._display = QLabel()

        self._slider.setRange(0, 255)
        self._control.setValidator(QDoubleValidator(0, 100, 1))

        self._attach_signals()
        self._do_layout(label)

    ###########################################################################
    # API method definitions
    ###########################################################################

    @info(True)
    def set_volume(self, vol: int) -> None:
        self._slider.setValue(vol)
        self._control.setText(f"{100 * vol / 255:5.1f}")
        self._display.setText(f"x{vol:02X}")
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
