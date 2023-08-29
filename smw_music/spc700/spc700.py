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

# Standard library imports
from dataclasses import dataclass
from enum import IntEnum, auto

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
) -> tuple[npt.NDArray[np.double], tuple[str, str, str, str]]:
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


###############################################################################


def generate_decexp(gain_reg: int) -> tuple[npt.NDArray[np.double], str]:
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


###############################################################################


def generate_declin(gain_reg: int) -> tuple[npt.NDArray[np.double], str]:
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


###############################################################################


def generate_direct_gain(gain_reg: int) -> tuple[npt.NDArray[np.double], str]:
    gain = (gain_reg << 4) / _LIMIT
    rv = f"{100*(gain_reg)/(_LIMIT >> 4):.2f}%"

    plot = np.array(([0, 100], [gain, gain]))

    return (plot, rv)


###############################################################################


def generate_incbent(gain_reg: int) -> tuple[npt.NDArray[np.double], str]:
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


###############################################################################


def generate_inclin(gain_reg: int) -> tuple[npt.NDArray[np.double], str]:
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


###############################################################################
# Private method definitions
###############################################################################


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


###############################################################################
# API class definitions
###############################################################################


class GainMode(IntEnum):
    DIRECT = auto()
    INCLIN = auto()
    INCBENT = auto()
    DECLIN = auto()
    DECEXP = auto()


###############################################################################


@dataclass
class Envelope:
    adsr_mode: bool = True
    attack_setting: int = 0
    decay_setting: int = 0
    sus_level_setting: int = 0
    sus_rate_setting: int = 0
    gain_mode: GainMode = GainMode.DIRECT
    gain_setting: int = 0

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_regs(
        cls, adsr1_reg: int, adsr2_reg: int, gain_reg: int
    ) -> "Envelope":
        adsr_mode = bool(adsr1_reg >> 7)
        attack_setting = 0xF & adsr1_reg
        decay_setting = 0x7 & (adsr1_reg >> 4)
        sus_level_setting = adsr2_reg >> 5
        sus_rate_setting = 0x1F & adsr2_reg

        if gain_reg & 0x80:
            gain_mode = GainMode.DIRECT
        else:
            match gain_reg >> 5:
                case 0b00:
                    gain_mode = GainMode.DECLIN
                case 0b01:
                    gain_mode = GainMode.DECEXP
                case 0b10:
                    gain_mode = GainMode.INCLIN
                case 0b11:
                    gain_mode = GainMode.INCBENT

        gain_mask = 0x7F if gain_mode == GainMode.DIRECT else 0x1F
        gain_setting = gain_reg & gain_mask

        return cls(
            adsr_mode,
            attack_setting,
            decay_setting,
            sus_level_setting,
            sus_rate_setting,
            gain_mode,
            gain_setting,
        )

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def adsr1_reg(self) -> int:
        rv = int(self.adsr_mode) << 7
        rv |= self.decay_setting << 4
        rv |= self.attack_setting
        return rv

    ###########################################################################

    @property
    def adsr2_reg(self) -> int:
        return (self.sus_level_setting << 5) | self.sus_rate_setting

    ###########################################################################

    @property
    def envelope(
        self,
    ) -> tuple[npt.NDArray[np.double], npt.NDArray[np.double]]:
        if self.adsr_mode:
            env, _ = generate_adsr(
                self.attack_setting,
                self.decay_setting,
                self.sus_level_setting,
                self.sus_rate_setting,
            )
        else:
            match self.gain_mode:
                case GainMode.DIRECT:
                    env, _ = generate_direct_gain(self.gain_setting)
                case GainMode.INCLIN:
                    env, _ = generate_inclin(self.gain_setting)
                case GainMode.INCBENT:
                    env, _ = generate_incbent(self.gain_setting)
                case GainMode.DECLIN:
                    env, _ = generate_declin(self.gain_setting)
                case GainMode.DECEXP:
                    env, _ = generate_decexp(self.gain_setting)

        return env[0], env[1]

    ###########################################################################

    @property
    def gain_reg(self) -> int:
        match self.gain_mode:
            case GainMode.DIRECT:
                rv = self.gain_setting
            case GainMode.INCLIN:
                rv = 0xC0 | self.gain_setting
            case GainMode.INCBENT:
                rv = 0xE0 | self.gain_setting
            case GainMode.DECLIN:
                rv = 0x80 | self.gain_setting
            case GainMode.DECEXP:
                rv = 0xA0 | self.gain_setting

        return rv
