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

###############################################################################
# Private function definitions
###############################################################################


def _mag_inv_to_int(mag: float, inv: bool) -> int:
    clip = min(max(mag, 0.0), 1.0)
    # The '0xFF &' forces the integer into 2's complement representation
    return 0xFF & round(-128 * clip if inv else 127 * clip)


###############################################################################
# API class definitions
###############################################################################


@dataclass
class EchoConfig:
    """
    Configuration settings for setting up echo/reverb

    Parameters
    ----------
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

    vol_mag: tuple[float, float]
    vol_inv: tuple[bool, bool]
    delay: int
    fb_mag: float
    fb_inv: bool
    fir_filt: int

    ###########################################################################
    # API constructor definitions
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
