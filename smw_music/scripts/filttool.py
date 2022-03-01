#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SNES Echo Filter Tool."""

###############################################################################
# Standard Library imports
###############################################################################

import argparse
import sys

###############################################################################
# Library imports
###############################################################################

import scipy.signal

import matplotlib.pyplot as plt
import numpy as np

from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QLineEdit,
    QMainWindow,
    QSlider,
    QWidget,
)

import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

###############################################################################
# Package imports
###############################################################################

from smw_music import __version__

###############################################################################
# Private function definitions
###############################################################################


def _decode_coeffs(arg: str) -> np.ndarray:
    coeffs = list(int(x, 0) for x in arg.split(","))

    return np.array(coeffs, dtype=np.int8)


###############################################################################
# API function definitions
###############################################################################


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=500, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.mag = self.fig.add_subplot(2, 1, 1)
        self.phase = self.fig.add_subplot(2, 1, 2)

        self.mag.grid(True)
        self.phase.grid(True)

        super(MplCanvas, self).__init__(self.fig)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create the maptlotlib FigureCanvas object,
        # which defines a single set of axes as self.axes.
        self.sc = MplCanvas(self, width=5, height=4, dpi=100)

        widget = QWidget()

        layout = QGridLayout()
        layout.addWidget(self.sc, 0, 0, 1, 8)

        self.sliders = []
        self.controls = []
        for n in range(8):
            slider = QSlider()
            slider.setRange(-128, 127)
            layout.addWidget(slider, 1, n, 1, 1)
            slider.valueChanged.connect(
                lambda v, n=n: self._slider_updated(n, v)
            )
            self.sliders.append(slider)

            edit = QLineEdit("0")
            layout.addWidget(edit, 2, n, 1, 1)
            edit.editingFinished.connect(lambda n=n: self._control_updated(n))
            self.controls.append(edit)

        widget.setLayout(layout)

        self.setCentralWidget(widget)

        self.show()

    def _control_updated(self, idx: int) -> None:
        val = int(self.controls[idx].text(), 0)
        if val > 127:
            val -= 256
        self.sliders[idx].setValue(val)

    def _slider_updated(self, idx: int, val: int) -> None:
        self.controls[idx].setText(f"0x{(0xff & val):02x}")

        coeffs = [slider.value() for slider in self.sliders]
        self.update(np.array(coeffs, dtype=np.int8))

    def update(self, coeffs) -> None:
        w, mag, phase = scipy.signal.dbode(
            (coeffs / 128, 1, 1 / (8e3)), n=1000
        )
        phase = (phase + 180) % 360 - 180
        w /= 2 * np.pi
        plt.figure()

        self.sc.mag.cla()
        self.sc.mag.semilogx(w, mag)
        self.sc.mag.set_ylim(-60, max(10, np.max(mag)))
        self.sc.mag.set_xlabel("freq/Hz")
        self.sc.mag.set_ylabel("Mag/dB")
        # self.sc.mag.set_title("Magnitude Response")

        self.sc.phase.cla()
        self.sc.phase.semilogx(w, phase)
        self.sc.phase.set_ylim(-210, 210)
        self.sc.phase.set_xlabel("freq/Hz")
        self.sc.phase.set_ylabel("Phase/\u00b0")
        # self.sc.phase.set_title("Phase Response")

        self.sc.fig.canvas.draw_idle()


###############################################################################


def main(args=None):
    """Entrypoint for Echo Filter Tool."""
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description=f"SNES Echo Filter Tool v{__version__}"
    )

    args = parser.parse_args(args)

    matplotlib.use("Qt5Agg")

    app = QApplication(sys.argv)
    w = MainWindow()
    app.exec()


###############################################################################
# Entrypoint
###############################################################################

if __name__ == "__main__":
    main()
