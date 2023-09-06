# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

# conversions from: https://www.romhacking.net/download/documents/191/

###############################################################################
# Imports
###############################################################################

# Library imports
import pyqtgraph as pg  # type: ignore
from PyQt6.QtWidgets import QHBoxLayout, QWidget

# Package imports
from smw_music import spc700

###############################################################################
# API class definitions
###############################################################################


class EnvelopePreview(QWidget):
    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._graph = pg.PlotWidget()
        self._graph.setBackground("w")

        # plot data: x, y values
        self._plot_data = self._graph.plot(
            [], [], pen={"color": "k", "width": 3}
        )
        self._graph.setLabel("bottom", "s")
        self._graph.setLabel("left", "gain")
        self._graph.setYRange(0, 1)
        self._graph.setXRange(0, 0.1)
        self._graph.setMouseEnabled(y=False)

        layout = QHBoxLayout()
        layout.addWidget(self._graph)

        self.setLayout(layout)

    ###########################################################################
    # API method definitions
    ###########################################################################

    def plot_adsr(
        self,
        attack_reg: int,
        decay_reg: int,
        slevel_reg: int,
        srate_reg: int,
    ) -> tuple[str, str, str, str]:
        plot, (
            attack_str,
            decay_str,
            slevel_str,
            release_str,
        ) = spc700.generate_adsr(attack_reg, decay_reg, slevel_reg, srate_reg)

        self._plot_data.setData(plot[0], plot[1])

        return (attack_str, decay_str, slevel_str, release_str)

    ###########################################################################

    def plot_decexp(self, gain_reg: int) -> str:
        plot, rv = spc700.generate_decexp(gain_reg)

        self._plot_data.setData(plot[0], plot[1])
        return rv

    ###########################################################################

    def plot_declin(self, gain_reg: int) -> str:
        plot, rv = spc700.generate_declin(gain_reg)

        self._plot_data.setData(plot[0], plot[1])
        return rv

    ###########################################################################

    def plot_direct_gain(self, gain_reg: int) -> str:
        plot, rv = spc700.generate_direct_gain(gain_reg)
        self._plot_data.setData(plot[0], plot[1])

        return rv

    ###########################################################################

    def plot_incbent(self, gain_reg: int) -> str:
        plot, rv = spc700.generate_incbent(gain_reg)
        self._plot_data.setData(plot[0], plot[1])

        return rv

    ###########################################################################

    def plot_inclin(self, gain_reg: int) -> str:
        plot, rv = spc700.generate_inclin(gain_reg)
        self._plot_data.setData(plot[0], plot[1])

        return rv
