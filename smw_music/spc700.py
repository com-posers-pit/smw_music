# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""
Logic related to the SPC700 chip
"""

###############################################################################
# Imports
###############################################################################

# Library imports
import numpy as np
import numpy.typing as npt

###############################################################################
# API constant definitions
###############################################################################

PITCH_REG_SCALE = 2**12
SAMPLE_FREQ = 32000

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
# API function definitions
###############################################################################


def generate_adsr(
    attack_reg: int,
    decay_reg: int,
    slevel_reg: int,
    srate_reg: int,
) -> tuple[npt.NDArray[float], tuple[str, str, str, str]]:
    times = [0.0, 0.0]
    envelope = [0.0, 1.0]

    # Attack
    attack = 2 * attack_reg + 1
    slope = 32 if attack_reg != 0xF else 1024
    attack_done = _propagate(attack, (0, 0), 1, slope)
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
            right = _propagate(decay, (left, top), bottom, slope)
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
            right = _propagate(srate, (left, top), bottom, slope)
            times.append(right)
            envelope.append(bottom)
        release_done = times[-1]
        release_str = _time_to_str(release_done - decay_done)
    else:
        release_str = "∞"

    times.append(100)
    envelope.append(envelope[-1])

    plot = np.array((times, envelope))

    return (plot, (attack_str, decay_str, slevel_str, release_str))


###########################################################################


def generate_decexp(gain_reg: int) -> tuple[npt.NDArray[float], str]:
    times = [0.0]
    envelope = [1.0]

    if gain_reg:
        for n in range(16):
            top = envelope[-1]
            left = times[-1]
            bottom = (15 - n) / 16
            slope = -(16 - n)
            right = _propagate(gain_reg, (left, top), bottom, slope)
            times.append(right)
            envelope.append(bottom)

        rv = _time_to_str(times[-1])
    else:
        rv = "∞"

    times.append(100)
    envelope.append(envelope[-1])
    plot = np.array((times, envelope))

    return (plot, rv)


###########################################################################


def generate_declin(gain_reg: int) -> tuple[npt.NDArray[float], str]:
    times = [0.0, 0.0, 100]
    envelope = [1, 0, 0]

    times[1] = _propagate(gain_reg, (0, 1), 0, -32)
    rv = _time_to_str(times[1])
    if gain_reg == 0:
        rv = "∞"
        times[1] = 100
        envelope[1] = 1
        envelope[2] = 1

    plot = np.array((times, envelope))
    return (plot, rv)


###########################################################################


def generate_direct_gain(gain_reg: int) -> tuple[npt.NDArray[float], str]:
    gain = (gain_reg << 4) / _LIMIT
    rv = f"{100*(gain_reg)/(_LIMIT >> 4):.2f}%"

    plot = np.array(([0, 100], [gain, gain]))

    return (plot, rv)


###########################################################################


def generate_incbent(gain_reg: int) -> str:
    times = [0.0, 0.0, 0.0, 100]
    envelope = [0, 0.75, 1, 1]

    times[1] = _propagate(gain_reg, (0, 0), 0.75, 32)
    times[2] = _propagate(gain_reg, (times[1], 0.75), 1, 8)
    rv = _time_to_str(times[2])

    if gain_reg == 0:
        rv = "∞"
        times[1] = 100
        times[2] = 100
        envelope[1] = 0
        envelope[2] = 0
        envelope[3] = 0

    plot = np.array((times, envelope))
    return (plot, rv)


###########################################################################


def generate_inclin(gain_reg: int) -> str:
    times = [0.0, 0.0, 100]
    envelope = [0, 1, 1]

    times[1] = _propagate(gain_reg, (0, 0), 1, 32)
    rv = _time_to_str(times[1])

    if gain_reg == 0:
        rv = "∞"
        times[1] = 100
        envelope[1] = 0
        envelope[2] = 0

    plot = np.array((times, envelope))

    return (plot, rv)


###########################################################################
# Private method definitions
###########################################################################


def _propagate(
    gain_reg: int,
    start: tuple[float, float],
    target: float,
    slope: int,
) -> float:
    period = _RATES[gain_reg]
    offset = _OFFSETS[gain_reg]

    nstep = ((target - start[1]) * (_LIMIT + 1)) // slope
    return start[0] + (nstep * period - (offset % period)) / SAMPLE_FREQ
