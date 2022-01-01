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

import wave

from collections import deque
from dataclasses import dataclass
from typing import Optional

###############################################################################
# Library imports
###############################################################################

import numpy as np
import numpy.typing as npt

###############################################################################
# Package imports
###############################################################################

from . import SmwMusicException

###############################################################################
# Private constant definitions
###############################################################################

_PRESCALE = 64

# Filter coefficients documented in [1]
_FILTERS = {
    0: tuple(_PRESCALE * x for x in (0, 0)),
    1: tuple(_PRESCALE * x for x in (0.9375, 0.0)),
    2: tuple(_PRESCALE * x for x in (1.90625, -0.9375)),
    3: tuple(_PRESCALE * x for x in (1.796875, -0.8125)),
}

###############################################################################
# Private function definitions
###############################################################################


def _u4_to_s4(data: npt.NDArray[np.uint8]) -> npt.NDArray[np.int8]:
    return (0xF & (data.astype(np.int8) + 8)) - 8


###############################################################################
# API class definitions
###############################################################################


class BrrException(SmwMusicException):
    """BRR Handling Exceptions."""


###############################################################################


@dataclass
class Brr:
    blocks: npt.NDArray[np.uint8]
    loop_point: Optional[int] = None

    ###########################################################################
    # API constructor definitions
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
    # API method definitions
    ###########################################################################

    def generate_waveform(self, loops: int = 1) -> npt.NDArray[np.int16]:

        samples = np.zeros(16, dtype=np.int8)
        rv = []
        x = deque([0, 0], 2)  # pylint: disable=invalid-name

        start_block = 0
        for _ in range(loops):
            for block in self.blocks[start_block:]:
                range_val = block[0] >> 4
                filter_val = 0x3 & (block[0] >> 2)
                samples[0::2] = _u4_to_s4(0xF & (block[1:] >> 4))
                samples[1::2] = _u4_to_s4(0xF & block[1:])

                row = []
                for sample in samples:
                    rval = sample << range_val

                    a, b = _FILTERS[filter_val]  # pylint: disable=invalid-name

                    x.appendleft(
                        (_PRESCALE * rval + a * x[0] + b * x[1]) // _PRESCALE
                    )

                    row.append(x[0])

                rv.append(row)

            start_block = self.loop_block

        return np.array(rv, dtype=np.int16).reshape(-1)

    ###########################################################################

    def to_wav(self, fname: str, loops: int = 0, framerate: int = 8000):
        with wave.open(fname, "wb") as fobj:
            fobj.setnchannels(1)  # pylint: disable=no-member
            fobj.setsampwidth(2)  # pylint: disable=no-member
            fobj.setframerate(framerate)  # pylint: disable=no-member
            fobj.writeframesraw(  # pylint: disable=no-member
                self.generate_waveform(loops).tobytes()
            )

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
            "Range,Filter,Loop,End,S1,S2,S3,S4,S5,S6,S7,S8,"
            + "S9,S10,S11,S12,S13,S14,S15,S16"
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
    def loop_block(self) -> int:
        return 0 if self.loop_point is None else self.loop_point // 9

    ###########################################################################
    # Data model methods
    ###########################################################################

    def __post_init__(self):
        if self.loop_point is not None:
            valid_len = self.loop_point % 9 == 0
            valid_block = 0 <= self.loop_point < self.blocks.size

            if not (valid_len and valid_block):
                raise BrrException(f"Invalid loop point: {self.loop_point}")

    ###########################################################################
