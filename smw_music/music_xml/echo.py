#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Echo configuration logic."""

###############################################################################
# Standard Library imports
###############################################################################

from dataclasses import dataclass
from typing import Set, Tuple


###############################################################################
# Private function definitions
###############################################################################


def _truthy(arg: str) -> bool:
    return bool(arg.lower() in ["1", "true", "t", "y"])


###############################################################################
# API class definitions
###############################################################################


@dataclass(frozen=True)
class EchoConfig:
    chan_list: Set[int]
    vol_mag: Tuple[int, int]
    vol_inv: Tuple[bool, bool]
    delay: int
    rev_mag: int
    rev_inv: bool
    fir_filt: int

    @classmethod
    def from_csv(cls, csv: str) -> "EchoConfig":
        fields = csv.split(",")

        fir_filt = int(fields.pop())
        rev_inv = _truthy(fields.pop())
        rev_mag = int(fields.pop())
        delay = int(fields.pop())

        rvol_inv = _truthy(fields.pop())
        rvol_mag = int(fields.pop())
        lvol_inv = _truthy(fields.pop())
        lvol_mag = int(fields.pop())

        chan_list = set(map(int, fields))

        return cls(
            chan_list,
            (lvol_mag, rvol_mag),
            (lvol_inv, rvol_inv),
            delay,
            rev_mag,
            rev_inv,
            fir_filt,
        )

    @property
    def channels(self):
        return sum(2 ** x for x in self.chan_list)

    @property
    def left_vol(self):
        return 0xFF & (self.vol_mag[0] * (-1) ** self.vol_inv[0])

    @property
    def right_vol(self):
        return 0xFF & (self.vol_mag[1] * (-1) ** self.vol_inv[1])

    @property
    def reverb(self):
        return 0xFF & (self.rev_mag * (-1) ** self.rev_inv)
