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
import pyqtgraph as pg  # type: ignore
from PyQt6.QtWidgets import QMainWindow, QWidget

###############################################################################
# Private constant definition
###############################################################################

# fmt: off
_LIMIT = 2**11 - 1
_MAX_COUNT = 0x77ff
_MAX_SECS = 38
_OFFSETS = [0,   0, 1040,
            536, 0, 1040,
            536, 0, 1040,
            536, 0, 1040,
            536, 0, 1040,
            536, 0, 1040,
            536, 0, 1040,
            536, 0, 1040,
            536, 0, 1040,
            536, 0, 1040,
            0,   0]
_RATES = [2**32,   # "infinity"
          2048, 1536, 1280, 1024, 768, 640, 512, 384, 320, 256, 192, 160,
          128, 96, 80, 64, 48, 40, 32, 24, 20, 16, 12, 10, 8, 6, 5, 4, 3, 2, 1]
_SAMPLE_FREQ = 32000
# fmt: on

###############################################################################
# Private function definitions
###############################################################################


def _time_to_str(tval: float) -> str:
    if tval < 1:
        rv = f"{int(1000*tval)}ms"
    else:
        rv = f"{tval:.1f}s"
    return rv


###############################################################################
# Private class definitions
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

    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._graph = pg.PlotWidget()
        self.setCentralWidget(self._graph)
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
        self.setWindowTitle("Envelope Preview")

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
        times = [0.0, 0.0]
        envelope = [0.0, 1.0]

        # Attack
        attack = 2 * attack_reg + 1
        slope = 32 if attack_reg != 0xF else 1024
        attack_done = self._propagate(attack, (0, 0), 1, slope)
        times[1] = attack_done
        attack_str = _time_to_str(times[1])

        # Decay
        decay = 2 * decay_reg + 16
        slevel = 2 * (slevel_reg + 1)
        if slevel:
            for n in range(16 - slevel):
                top = envelope[-1]
                left = times[-1]
                bottom = (15 - n) / 16
                slope = -(16 - n)
                right = self._propagate(decay, (left, top), bottom, slope)
                times.append(right)
                envelope.append(bottom)
            decay_done = times[-1]
            decay_str = _time_to_str(decay_done - attack_done)
        else:
            decay_done = times[-1]
            decay_str = "∞"

        # "Sustain"
        slevel_str = f"{slevel_reg + 1}/8"
        srate = srate_reg
        if srate:
            for n in range(16 - slevel, 16):
                top = envelope[-1]
                left = times[-1]
                bottom = (15 - n) / 16
                slope = -(16 - n)
                right = self._propagate(srate, (left, top), bottom, slope)
                times.append(right)
                envelope.append(bottom)
            release_done = times[-1]
            release_str = _time_to_str(release_done - decay_done)
        else:
            release_str = "∞"

        times.append(100)
        envelope.append(envelope[-1])

        self._plot_data.setData(times, envelope)

        return (attack_str, decay_str, slevel_str, release_str)

    ###########################################################################

    def plot_decexp(self, gain_reg: int) -> str:
        times = [0.0]
        envelope = [1.0]

        if gain_reg:
            for n in range(16):
                top = envelope[-1]
                left = times[-1]
                bottom = (15 - n) / 16
                slope = -(16 - n)
                right = self._propagate(gain_reg, (left, top), bottom, slope)
                times.append(right)
                envelope.append(bottom)

            rv = _time_to_str(times[-1])
        else:
            rv = "∞"

        times.append(100)
        envelope.append(envelope[-1])
        self._plot_data.setData(times, envelope)
        return rv

    ###########################################################################

    def plot_declin(self, gain_reg: int) -> str:
        times = [0.0, 0.0, 100]
        envelope = [1, 0, 0]

        times[1] = self._propagate(gain_reg, (0, 1), 0, -32)
        rv = _time_to_str(times[1])
        if gain_reg == 0:
            rv = "∞"
            times[1] = 100
            envelope[1] = 1
            envelope[2] = 1

        self._plot_data.setData(times, envelope)
        return rv

    ###########################################################################

    def plot_direct_gain(self, gain_reg: int) -> str:
        gain = (gain_reg << 4) / _LIMIT
        self._plot_data.setData([0, 100], [gain, gain])

        return f"{100*(gain_reg)/(_LIMIT >> 4):.2f}%"

    ###########################################################################

    def plot_incbent(self, gain_reg: int) -> str:
        times = [0.0, 0.0, 0.0, 100]
        envelope = [0, 0.75, 1, 1]

        times[1] = self._propagate(gain_reg, (0, 0), 0.75, 32)
        times[2] = self._propagate(gain_reg, (times[1], 0.75), 1, 8)
        rv = _time_to_str(times[2])

        if gain_reg == 0:
            rv = "∞"
            times[1] = 100
            times[2] = 100
            envelope[1] = 0
            envelope[2] = 0
            envelope[3] = 0

        self._plot_data.setData(times, envelope)
        return rv

    ###########################################################################

    def plot_inclin(self, gain_reg: int) -> str:
        times = [0.0, 0.0, 100]
        envelope = [0, 1, 1]

        times[1] = self._propagate(gain_reg, (0, 0), 1, 32)
        rv = _time_to_str(times[1])

        if gain_reg == 0:
            rv = "∞"
            times[1] = 100
            envelope[1] = 0
            envelope[2] = 0

        self._plot_data.setData(times, envelope)
        return rv

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _propagate(
        self,
        gain_reg: int,
        start: tuple[float, float],
        target: float,
        slope: int,
    ) -> float:
        period = _RATES[gain_reg]
        offset = _OFFSETS[gain_reg]

        nstep = ((target - start[1]) * (_LIMIT + 1)) // slope
        return start[0] + (nstep * period - (offset % period)) / _SAMPLE_FREQ
