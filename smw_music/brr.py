# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""
Utilities for handling BRR files.

Notes
-----
Decoding algorithm is documented in [1]_.

File loop headers are discussed in [2]_.

.. [1] SNES Dev Manual Book 1 (Fixed ToC) : Nintendo : Free Download, Borrow,
       and Streaming : Internet Archive.
       https://archive.org/details/snes_manual1

.. [2] Trouble Creating Samples (Solved) - Custom Music - SMW Central.
       https://www.smwcentral.net/?p=viewthread&t=76768&page=1&pid=1192147#p1192147
"""

###############################################################################
# Standard Library imports
###############################################################################

from typing import Optional

###############################################################################
# Library imports
###############################################################################

import numpy as np

###############################################################################
# Project imports
###############################################################################

from . import SmwMusicException

###############################################################################
# Private function definitions
###############################################################################


def _u4_to_s4(data: np.ndarray) -> np.ndarray:
    return (0xF & (data.astype(np.int8) + 8)) - 8


###############################################################################
# API class definitions
###############################################################################


class BrrException(SmwMusicException):
    """BRR Handling Exceptions."""


###############################################################################


class Brr:

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    def __init__(self, blocks: np.ndarray, loop_point: Optional[int] = None):
        self.blocks = blocks
        self.loop_point = loop_point

    ###########################################################################

    @classmethod
    def from_binary(cls, raw: bytes) -> "Brr":
        data = np.frombuffer(raw, np.uint8)
        if data.size % 9 == 0:
            start = 0
            loop_point = None
        elif (data.size - 2) % 9 == 0:
            start = 2
            # Little endian per [2] above
            loop_point = int.from_bytes(raw[:2], "little")

        data = data[start:].reshape((-1, 9))
        return cls(data, loop_point)

    ###########################################################################

    @classmethod
    def from_file(cls, fname: str) -> "Brr":
        with open(fname, "rb") as fobj:
            return cls.from_binary(fobj.read())

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def binary(self) -> bytes:
        rv = b""
        if self.loop_point is not None:
            rv += self.loop_point.to_bytes(2, "little")

        return self.blocks.tobytes()

    ###########################################################################

    @property
    def csv(self) -> str:
        rv = [
            "Range,Filter,Loop,End,S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12,S13,S14,S15,S16"
        ]

        data = 20 * [0]
        for block in self.blocks:
            range_val = block[0] >> 4
            filter_val = 0x3 & (block[0] >> 2)
            loop = bool(block[0] & 0x2)
            end = bool(block[0] & 0x1)
            data[0:4] = [range_val, filter_val, loop, end]
            data[4::2] = _u4_to_s4(0xF & (block[1:] >> 4))
            data[5::2] = _u4_to_s4(0xF & block[1:])
            rv.append(",".join(str(d) for d in data))

        return "\n".join(rv)

    ###########################################################################

    @property
    def decoded(self) -> np.ndarray:
        prescale = 64
        samples = np.zeros(16, dtype=np.int8)
        nrows = self.blocks.shape[0]
        rv = np.zeros((nrows, 16), dtype=np.int16)

        x = [0, 0]
        for row, block in enumerate(self.blocks):
            range_val = block[0] >> 4
            filter_val = 0x3 & (block[0] >> 2)
            samples[0::2] = _u4_to_s4(0xF & (block[1:] >> 4))
            samples[1::2] = _u4_to_s4(0xF & block[1:])

            for col, sample in enumerate(samples):
                rval = sample << range_val

                # Filter coefficients documented in [1]  We use a prescalar so
                # we stay in integer arithmetic.
                if filter_val == 0:
                    a, b = 0.0, 0.0
                elif filter_val == 1:
                    a, b = 0.9375, 0.0
                elif filter_val == 2:
                    a, b = 1.90625, -0.9375
                else:  # filter_val == 3:
                    a, b = 1.796875, -0.8125

                a, b = int(prescale * a), int(prescale * b)

                xval = (prescale * rval + a * x[0] + b * x[1]) // prescale

                x = [xval, x[0]]
                rv[row, col] = xval

        rv.shape = (-1,)
        return rv
