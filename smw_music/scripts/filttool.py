#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SNES Echo Filter Tool."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
# Standard Library imports
import argparse
import sys
import warnings
from functools import partial
from typing import Any, Optional, cast

# Library imports
import matplotlib  # type: ignore
import numpy as np
import numpy.typing as npt
import scipy.signal  # type: ignore
from matplotlib.backends.backend_qt5agg import (  # type: ignore
    FigureCanvasQTAgg,
)
from matplotlib.figure import Figure  # type: ignore
from matplotlib.ticker import ScalarFormatter  # type: ignore
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

# Package imports
from smw_music import __version__

###############################################################################
###############################################################################


###############################################################################
# Private function definitions
###############################################################################


def _decode_coeffs(arg: str) -> npt.NDArray[np.int8]:
    coeffs = list(int(x, 0) for x in arg.split(","))

    return np.array(coeffs, dtype=np.int8)


###############################################################################
# API function definitions
###############################################################################


# Type info is missing, so we have to ignore typing in the subclassing
class MplCanvas(FigureCanvasQTAgg):  # type: ignore
    def __init__(
        self,
        parent: Optional[QWidget] = None,  # pylint: disable=unused-argument
        width: int = 5,
        height: int = 1000,
        dpi: int = 200,
    ):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.mag = self.fig.add_subplot(2, 1, 1)
        self.phase = self.fig.add_subplot(2, 1, 2)

        self.mag.grid(True)
        self.phase.grid(True)

        super(MplCanvas, self).__init__(self.fig)


###############################################################################


def _update_slider_from_button(slider: QSlider, val: int, _: bool) -> None:
    slider.setValue(val)


###############################################################################


class MainWindow(QMainWindow):
    canvas: MplCanvas
    controls: list[QLineEdit]
    sliders: list[QSlider]

    ###########################################################################

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        # Create the maptlotlib FigureCanvas object,
        # which defines a single set of axes as self.axes.
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)

        widget = QWidget()

        grid = QGridLayout()
        grid.addWidget(self.canvas, 0, 0, 1, 8)
        grid.setRowStretch(0, 3)
        grid.setRowStretch(1, 1)

        ncoeff = 8
        self.sliders = []
        self.controls = []

        for n in range(ncoeff):
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.Box)

            layout = QVBoxLayout()

            label = QLabel(f"C{n}")
            layout.addWidget(label)
            layout.setAlignment(label, QtCore.Qt.AlignmentFlag.AlignHCenter)

            slider = QSlider()
            slider.setRange(-128, 127)
            slider.setPageStep(16)
            layout.addWidget(slider)
            layout.setAlignment(slider, QtCore.Qt.AlignmentFlag.AlignHCenter)
            slider.valueChanged.connect(
                lambda v, n=n: self._slider_updated(n, v)
            )
            self.sliders.append(slider)

            edit = QLineEdit("0")
            layout.addWidget(edit)
            edit.editingFinished.connect(lambda n=n: self._control_updated(n))
            self.controls.append(edit)

            btn = QPushButton("Max")
            layout.addWidget(btn)
            btn.clicked.connect(
                partial(_update_slider_from_button, slider, 127)
            )

            btn = QPushButton("Zero")
            layout.addWidget(btn)
            btn.clicked.connect(partial(_update_slider_from_button, slider, 0))

            btn = QPushButton("Min")
            layout.addWidget(btn)
            btn.clicked.connect(
                partial(_update_slider_from_button, slider, -128)
            )

            frame.setLayout(layout)
            grid.addWidget(frame, 1, n, 1, 1)

        widget.setLayout(grid)

        for lst in (self.sliders, self.controls):
            lst = cast(list[QWidget], lst)
            for this, nxt in zip(lst, lst[1:]):
                QWidget.setTabOrder(this, nxt)

        self.setCentralWidget(widget)

        self.show()

    ###########################################################################

    def _control_updated(self, idx: int) -> None:
        val = int(self.controls[idx].text(), 0)
        if val > 127:
            val -= 256
        self.sliders[idx].setValue(val)

    ###########################################################################

    def _slider_updated(self, idx: int, val: int) -> None:
        self.controls[idx].setText(f"0x{(0xff & val):02x}")

        coeffs = [slider.value() for slider in self.sliders]
        self.update_plot(np.array(coeffs, dtype=np.int8))

    ###########################################################################

    def update_plot(self, coeffs: npt.NDArray[np.int8]) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            w, mag, phase = scipy.signal.dbode(
                (coeffs[::-1] / 128, 1, 1 / (8e3)), n=1000
            )

        phase = (phase + 180) % 360 - 180
        w /= 2 * np.pi

        axes = self.canvas.mag
        axes.cla()
        axes.semilogx(w, mag)
        axes.grid(True)
        axes.set_ylim(max(-60, np.min(mag) - 10), 10 + max(0, np.max(mag)))
        axes.set_xlabel("freq/Hz")
        axes.set_ylabel("Mag/dB")
        axes.set_title("Magnitude Response")
        axes.xaxis.set_major_formatter(ScalarFormatter())
        axes.set_xticks(
            [1, 2, 4, 7, 10, 20, 40, 70, 100, 200, 400, 700, 1000, 2000, 4000]
        )

        axes = self.canvas.phase
        axes.cla()
        axes.semilogx(w, phase)
        axes.grid(True)
        axes.set_ylim(-210, 210)
        axes.set_xlabel("freq/Hz")
        axes.set_ylabel("Phase/\u00b0")
        axes.set_title("Phase Response")
        axes.xaxis.set_major_formatter(ScalarFormatter())
        axes.set_xticks(
            [1, 2, 4, 7, 10, 20, 40, 70, 100, 200, 400, 700, 1000, 2000, 4000]
        )

        self.canvas.fig.canvas.draw_idle()
        self.canvas.fig.tight_layout()


###############################################################################


def main(arg_list: Optional[list[str]] = None) -> None:
    """Entrypoint for Echo Filter Tool."""
    if arg_list is None:
        arg_list = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description=f"SNES Echo Filter Tool v{__version__}"
    )

    _ = parser.parse_args(arg_list)  # pylint: disable=unused-variable

    matplotlib.use("Qt5Agg")

    app = QApplication(sys.argv)
    _ = MainWindow()  # pylint: disable=unused-variable
    app.exec()


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
