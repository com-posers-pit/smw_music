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

import warnings

###############################################################################
# Library imports
###############################################################################

import scipy.signal  # type: ignore

import matplotlib.pyplot as plt  # type: ignore
import numpy as np

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

import matplotlib
from matplotlib.backends.backend_qt5agg import (  # type: ignore
    FigureCanvasQTAgg,
)
from matplotlib.figure import Figure  # type: ignore

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
    def __init__(self, parent=None, width=5, height=1000, dpi=200):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.mag = self.fig.add_subplot(2, 1, 1)
        self.phase = self.fig.add_subplot(2, 1, 2)

        self.mag.grid(True)
        self.phase.grid(True)

        super(MplCanvas, self).__init__(self.fig)


###############################################################################


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create the maptlotlib FigureCanvas object,
        # which defines a single set of axes as self.axes.
        self.sc = MplCanvas(self, width=5, height=4, dpi=100)

        widget = QWidget()

        grid = QGridLayout()
        grid.addWidget(self.sc, 0, 0, 1, 8)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 0.5)

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
            btn.clicked.connect(lambda _, slider=slider: slider.setValue(127))

            btn = QPushButton("Zero")
            layout.addWidget(btn)
            btn.clicked.connect(lambda _, slider=slider: slider.setValue(0))

            btn = QPushButton("Min")
            layout.addWidget(btn)
            btn.clicked.connect(lambda _, slider=slider: slider.setValue(-128))

            frame.setLayout(layout)
            grid.addWidget(frame, 1, n, 1, 1)

        widget.setLayout(grid)

        for n in range(ncoeff - 1):
            for lst in [self.sliders, self.controls]:
                QWidget.setTabOrder(lst[n], lst[n + 1])

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
        self.update_plot(np.array(coeffs, dtype=np.int8))

    def update_plot(self, coeffs: np.ndarray) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            w, mag, phase = scipy.signal.dbode(
                (coeffs[::-1] / 128, 1, 1 / (8e3)), n=1000
            )

        phase = (phase + 180) % 360 - 180
        w /= 2 * np.pi

        self.sc.mag.cla()
        self.sc.mag.semilogx(w, mag)
        self.sc.mag.grid(True)
        self.sc.mag.set_ylim(
            max(-60, np.min(mag) - 10), 10 + max(0, np.max(mag))
        )
        self.sc.mag.set_xlabel("freq/Hz")
        self.sc.mag.set_ylabel("Mag/dB")
        self.sc.mag.set_title("Magnitude Response")

        self.sc.phase.cla()
        self.sc.phase.semilogx(w, phase)
        self.sc.phase.grid(True)
        self.sc.phase.set_ylim(-210, 210)
        self.sc.phase.set_xlabel("freq/Hz")
        self.sc.phase.set_ylabel("Phase/\u00b0")
        self.sc.phase.set_title("Phase Response")

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
