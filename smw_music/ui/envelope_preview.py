# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

# conversions from: https://www.romhacking.net/download/documents/191/

###############################################################################
# Imports
###############################################################################

# Standard library imports
from enum import IntEnum, auto

# Library imports
import numpy as np
import numpy.typing as npt
import pyqtgraph as pg
from PyQt6.QtWidgets import QGraphicsScene, QMainWindow, QWidget

###############################################################################
# Private constant definition
###############################################################################

# fmt: off
_LIMIT = 2**11 - 1
_MAX_COUNT = 0x77ff
_MAX_SECS = 38
_OFFSETS = [0, 0, 1040, 536, 0, 1040, 536, 0, 1040, 536, 0, 1040, 536, 0, 1040,
            536, 0, 1040, 536, 0, 1040, 536, 0, 1040, 536, 0, 1040, 536, 0,
            1040, 0, 0]
_RATES = [2**32,   # "infinity"
          2048, 1536, 1280, 1024, 768, 640, 512, 384, 320, 256, 192, 160,
          128, 96, 80, 64, 48, 40, 32, 24, 20, 16, 12, 10, 8, 6, 5, 4, 3, 2, 1]
_SAMPLE_FREQ = 32000
# fmt: on

###############################################################################
# Private class definition
###############################################################################


class _AdsrState(IntEnum):
    ATTACK = auto()
    DECAY = auto()
    SUSTAIN = auto()
    RELEASE = auto()


###############################################################################
# API class definitions
###############################################################################


class EnvelopePreview(QMainWindow):
    _window: QMainWindow
    _graph: pg.PlotWidget
    _plot_data: pg.graphicsItems.PlotDataItem.PlotDataItem
    _counts: npt.NDArray

    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._graph = pg.PlotWidget()
        self.setCentralWidget(self._graph)
        self._graph.setBackground("w")
        self._counts = np.tile(np.arange(_MAX_COUNT, -1, -1), _MAX_SECS)

        # plot data: x, y values
        self._plot_data = self._graph.plot(
            [], [], pen={"color": "k", "width": 3}
        )
        self._graph.setLabel("bottom", "s")
        self._graph.setLabel("left", "gain")
        self._graph.setYRange(0, 1)
        self._graph.setXRange(0, 0.1)
        self._graph.setMouseEnabled(y=False)

    ###########################################################################
    # API method definitions
    ###########################################################################

    def plot_adsr(
        self,
        attack_reg: int,
        decay_reg: int,
        slevel_reg: int,
        srate_reg: int,
    ) -> None:
        attack_period = _RATES[2 * attack_reg + 1]
        attack_offset = _OFFSETS[2 * attack_reg + 1]
        decay_period = _RATES[2 * decay_reg + 16]
        decay_offset = _OFFSETS[2 * decay_reg + 16]
        sustain_period = _RATES[srate_reg]
        sustain_offset = _OFFSETS[srate_reg]

        times = [0.0]
        envelope = [0.0]

        envx = 0
        state = _AdsrState.ATTACK
        for n, count in enumerate(self._counts):
            match state:
                case _AdsrState.ATTACK:
                    if (count + attack_offset) % attack_period == 0:
                        envx += 32 if attack_reg != 0xF else 1024
                        if envx >= _LIMIT:
                            envx = _LIMIT
                            times.append(n / _SAMPLE_FREQ)
                            envelope.append(1.0)
                            state = _AdsrState.DECAY
                case _AdsrState.DECAY:
                    if (count + decay_offset) % decay_period == 0:
                        envx -= ((envx - 1) >> 8) + 1
                        times.append(n / _SAMPLE_FREQ)
                        envelope.append(envx / _LIMIT)
                        if envx >> 8 == slevel_reg:
                            if srate_reg:
                                state = _AdsrState.SUSTAIN
                            else:
                                break
                case _AdsrState.SUSTAIN:
                    if (count + sustain_offset) % sustain_period == 0:
                        envx -= ((envx - 1) >> 8) + 1
                        envx = max(envx, 0)

                        times.append(n / _SAMPLE_FREQ)
                        envelope.append(envx / _LIMIT)
                        if envx == 0:
                            break
                case _AdsrState.RELEASE:
                    pass

        times.append(100)
        envelope.append(envelope[-1])

        self._plot_data.setData(times, envelope)

    ###########################################################################

    def plot_decexp(self, gain_reg: int) -> None:
        period = _RATES[gain_reg]
        offset = _OFFSETS[gain_reg]
        times = [0.0]
        envelope = [1.0]
        envx = _LIMIT
        for n, count in enumerate(self._counts):
            if (count + offset) % period == 0:
                envx -= ((envx - 1) >> 8) + 1
                times.append(n / _SAMPLE_FREQ)
                envelope.append(envx / _LIMIT)

                if envx <= 0:
                    break

        times.append(100)
        envelope.append(0)
        self._plot_data.setData(times, envelope)

    ###########################################################################

    def plot_declin(self, gain_reg: int) -> None:
        period = _RATES[gain_reg]
        offset = _OFFSETS[gain_reg]
        times = [0.0, 0.0, 100]
        envelope = [1, 0, 0]
        envx = _LIMIT
        for n, count in enumerate(self._counts):
            if (count + offset) % period == 0:
                envx -= 32
                if envx <= 0:
                    times[1] = n / _SAMPLE_FREQ
                    break

        self._plot_data.setData(times, envelope)

    ###########################################################################

    def plot_direct_gain(self, gain_reg: int) -> None:
        gain = (gain_reg << 4) / _LIMIT
        self._plot_data.setData([0, 100], [gain, gain])

    ###########################################################################

    def plot_incbent(self, gain_reg: int) -> None:
        period = _RATES[gain_reg]
        offset = _OFFSETS[gain_reg]
        times = [0.0, 0.0, 0.0, 100]
        envelope = [0, 0.75, 1, 1]
        envx = 0
        for n, count in enumerate(self._counts):
            if (count + offset) % period == 0:
                if envx < 0x600:
                    envx += 32
                    if envx >= 0x600:
                        times[1] = n / _SAMPLE_FREQ
                else:
                    envx += 8
                    if envx >= _LIMIT:
                        times[2] = n / _SAMPLE_FREQ
                        break

        self._plot_data.setData(times, envelope)

    ###########################################################################

    def plot_inclin(self, gain_reg: int) -> None:
        period = _RATES[gain_reg]
        offset = _OFFSETS[gain_reg]
        times = [0.0, 0.0, 100]
        envelope = [0, 1, 1]
        envx = 0
        for n, count in enumerate(self._counts):
            if (count + offset) % period == 0:
                envx += 32
                if envx >= _LIMIT:
                    times[1] = n / _SAMPLE_FREQ
                    break

        self._plot_data.setData(times, envelope)
