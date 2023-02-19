#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Echo configuration logic."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass
from enum import IntEnum

###############################################################################
# Private function definitions
###############################################################################


def _mag_inv_to_int(mag: float, inv: bool) -> int:
    clip = min(max(mag, 0.0), 1.0)
    # The '0xFF &' forces the integer into 2's complement representation
    return 0xFF & round(-128 * clip if inv else 127 * clip)


###############################################################################


def _truthy(arg: str) -> bool:
    return bool(arg.lower() in ["1", "true", "t", "y"])


###############################################################################
# API class definitions
###############################################################################


class EchoCh(IntEnum):
    CH0 = 0
    CH1 = 1
    CH2 = 2
    CH3 = 3
    CH4 = 4
    CH5 = 5
    CH6 = 6
    CH7 = 7


###############################################################################


@dataclass
class EchoConfig:
    """
    Configuration settings for setting up echo/reverb

    Parameters
    ----------
    enables: set
        The set of channels that start with echo on
    vol_mag: tuple
        The (left, right) echo volume magnitudes (0-127, inclusive)
    vol_inv: tuple
        The (left, right) phase inversion settings---True to enable, False to
        disable
    delay: int
        The echo delay time, in taps (16ms/tap, 0-15 inclusive) (EDL register)
    fb_mag: int
        The feedback magnitude (0-127, inclusive)
    fb_inv: bool
        The feedback phase inversion---True to enable, False to disable
    fir_filt: int
        FIR filter selection (0 and 1 supported)

    Attributes
    ----------
    enables: set
        The set of channels that start with echo on (0-7, inclusive)
    vol_mag: tuple
        The (left, right) echo volume magnitudes (0-127, inclusive)
    vol_inv: tuple
        The (left, right) phase inversion settings---True to enable, False to
        disable
    delay: int
        The echo delay time, in taps (16ms/tap, 0-15 inclusive) (EDL register)
    fb_mag: int
        The feedback magnitude (0-127, inclusive)
    fb_inv: bool
        The feedback phase inversion---True to enable, False to disable
    fir_filt: int
        FIR filter selection (0 and 1 supported)
    """

    enables: set[EchoCh]
    vol_mag: tuple[float, float]
    vol_inv: tuple[bool, bool]
    delay: int
    fb_mag: float
    fb_inv: bool
    fir_filt: int

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_csv(cls, csv: str) -> "EchoConfig":
        """
        Construct an EchoConfig object from a CSV definition

        Paramters
        ---------
        csv: str
            A comma separated string echo configuration definition.  The input
            starts with a list of the channels with echo enabled (0-7),
            followed by the left volume magnitude (float, 0-1), a truthy
            indicator for phase-inverting the left channel, the right volume
            magnitude (float, 0-1), a truthy indicator for phase-inverting
            the right channel, an echo delay (integer, 0-15), the feedback
            magnitude (float, 0-1), a truthy indicator for phase-inverting
            the feedback magnitude, and an FIR filter selection (0 or 1).

        Return
        ------
        EchoConfig
            The constructed echo configuration
        """
        fields = csv.split(",")

        fir_filt = int(fields.pop())
        fb_inv = _truthy(fields.pop())
        fb_mag = float(fields.pop())
        delay = int(fields.pop())

        rvol_inv = _truthy(fields.pop())
        rvol_mag = float(fields.pop())
        lvol_inv = _truthy(fields.pop())
        lvol_mag = float(fields.pop())

        enables = set(map(lambda x: EchoCh(int(x)), fields))

        return cls(
            enables,
            (lvol_mag, rvol_mag),
            (lvol_inv, rvol_inv),
            delay,
            fb_mag,
            fb_inv,
            fir_filt,
        )

    ###########################################################################

    @property
    def channel_reg(self) -> int:
        """Return the echo enabled channel (EON) register."""
        return sum(2**x.value for x in self.enables)

    ###########################################################################

    @property
    def left_vol_reg(self) -> int:
        """Return the echo left volume (EVOL(L)) register."""
        return _mag_inv_to_int(self.vol_mag[0], self.vol_inv[0])

    ###########################################################################

    @property
    def right_vol_reg(self) -> int:
        """Return the echo right volume (EVOL(R)) register."""
        return _mag_inv_to_int(self.vol_mag[1], self.vol_inv[1])

    ###########################################################################

    @property
    def fb_reg(self) -> int:
        """Return the feedback (EFB) register setting."""
        return _mag_inv_to_int(self.fb_mag, self.fb_inv)
