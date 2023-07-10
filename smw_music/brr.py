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

.. [3] scipy.signal.lfilter &#8212; SciPy v1.7.1 Manual.
       https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.lfilter.html
"""

###############################################################################
# Standard Library imports
###############################################################################

# Standard library imports
import math
import wave
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

# Library imports
import numpy as np
import numpy.typing as npt
from scipy.signal import find_peaks, lfilter, lfiltic  # type: ignore

# Package imports
from smw_music import SmwMusicException, nspc

###############################################################################
# API constant definitions
###############################################################################

BLOCK_SIZE = 9

SAMPLE_FREQ = 32000

SAMPLES_PER_BLOCK = 16

###############################################################################
# Private constant definitions
###############################################################################

# Filter coefficients documented in [1].  Coefficient signs (and leading 1s)
# are required as documented in [3].
_FILTERS = {
    0: np.array([1, 0, 0]),
    1: np.array([1, -0.9375, 0]),
    2: np.array([1, -1.90625, 0.9375]),
    3: np.array([1, -1.7968750, 0.8125]),
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
    loop_point: int | None = None
    _waveform_cache: dict[int, npt.NDArray[np.int16]] = field(
        init=False, repr=False, compare=False, default_factory=dict
    )

    ###########################################################################
    # API constructor definitions
    ###########################################################################

    @classmethod
    def from_binary(cls, raw: bytes) -> "Brr":
        data = np.frombuffer(raw, np.uint8)
        if data.size % BLOCK_SIZE == 0:
            start = 0
            loop_point = None
        elif (data.size - 2) % BLOCK_SIZE == 0:
            start = 2
            # Little endian per [2] above
            loop_point = int.from_bytes(raw[:2], "little")

        data = data[start:].reshape((-1, BLOCK_SIZE))
        return cls(data, loop_point)

    ###########################################################################

    @classmethod
    def from_file(cls, fname: Path) -> "Brr":
        with open(fname, "rb") as fobj:
            return cls.from_binary(fobj.read())

    ###########################################################################
    # API method definitions
    ###########################################################################

    def generate_waveform(self, loops: int = 1) -> npt.NDArray[np.int16]:
        # Cache lookup
        try:
            return self._waveform_cache[loops]
        except KeyError:
            # Not in the cache, do the calculation
            pass

        if not self.sample_loops and loops != 1:
            raise BrrException("Cannot loop non-looping sample")

        # Variable initialization
        nblocks = self.nblocks + (loops - 1) * (self.nblocks - self.loop_block)
        rv = np.empty((nblocks, SAMPLES_PER_BLOCK), dtype=np.int16)
        proc = np.zeros(SAMPLES_PER_BLOCK)
        rv_idx = 0

        # Loop the requested number of times, starting at block 0 the first
        # time and at the loop block all other times
        start_block = 0
        for _ in range(loops):
            for n in range(start_block, self.nblocks):
                # Get the filter coefficients
                a_coeffs = _FILTERS[self.filters[n]]
                b_coeffs = [2 ** self.ranges[n]]

                # Run the IIR filter
                init = lfiltic(b_coeffs, a_coeffs, [proc[-1], proc[-2]])
                proc, _ = lfilter(b_coeffs, a_coeffs, self.samples[n], zi=init)

                # Store the result
                rv[rv_idx] = np.round(proc)
                rv_idx += 1

            start_block = self.loop_block

        # Cache storage and return
        self._waveform_cache[loops] = rv.reshape(-1)
        return self._waveform_cache[loops]

    ###########################################################################

    def to_wav(self, fname: str, loops: int = 0, framerate: int = 32000):
        with wave.open(fname, "wb") as fobj:
            fobj.setnchannels(1)  # pylint: disable=no-member
            fobj.setsampwidth(2)  # pylint: disable=no-member
            fobj.setframerate(framerate)  # pylint: disable=no-member
            fobj.writeframesraw(  # pylint: disable=no-member
                self.generate_waveform(loops).tobytes()
            )

    ###########################################################################

    def tune(
        self, note: int, target: float, fundamental: float = -1
    ) -> tuple[int, float]:
        if fundamental < 0:
            fundamental = self.fundamental
        return nspc.calc_tune(fundamental, note, target)

    ###########################################################################
    # API property definitions
    ###########################################################################

    @cached_property
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
        for n, (rval, fval, block) in enumerate(
            zip(self.ranges, self.filters, self.samples)
        ):
            loop = bool(self.blocks[n, 0] & 0x2)
            end = bool(self.blocks[n, 0] & 0x1)
            data = [rval, fval, loop, end, *block]
            rv.append(",".join(str(d) for d in data))

        return "\n".join(rv)

    ###########################################################################

    @cached_property
    def fundamental(self) -> float:
        samples_per_loop = SAMPLES_PER_BLOCK * (self.nblocks - self.loop_block)
        target_samples = 64000
        if self.sample_loops and samples_per_loop > 0:
            loops = math.ceil(target_samples / samples_per_loop)
            start = self.loop_block * SAMPLES_PER_BLOCK
        else:
            loops = 1
            start = 0

        nyquist = SAMPLE_FREQ / 2
        waveform = self.generate_waveform(loops)
        spec = np.abs(np.fft.rfft(waveform[start:]))
        spec /= spec.max()
        peak, *_ = find_peaks(spec, height=0.25)[0]
        return nyquist * peak / len(spec)

    ###########################################################################

    @cached_property
    def filters(self) -> list[int]:
        return list(0x3 & (self.blocks[:, 0] >> 2))

    ###########################################################################

    @cached_property
    def loop_block(self) -> int:
        return 0 if self.loop_point is None else self.loop_point // BLOCK_SIZE

    ###########################################################################

    @property
    def nblocks(self) -> int:
        return self.blocks.shape[0]

    ###########################################################################

    @cached_property
    def ranges(self) -> list[int]:
        return list(0xF & (self.blocks[:, 0] >> 4))

    ###########################################################################

    @cached_property
    def sample_loops(self) -> bool:
        return bool(self.blocks[-1, 0] & 2)

    ###########################################################################

    @cached_property
    def samples(self) -> npt.NDArray[np.int8]:
        evens = 0xF & (self.blocks[:, 1:] >> 4)
        odds = 0xF & (self.blocks[:, 1:])

        rv = np.empty((evens.shape[0], 16), dtype=np.int8)
        rv[:, ::2] = evens
        rv[:, 1::2] = odds

        return _u4_to_s4(rv)

    ###########################################################################
    # Data model methods
    ###########################################################################

    def __post_init__(self):
        if self.sample_loops and self.loop_point is not None:
            valid_len = self.loop_point % BLOCK_SIZE == 0
            valid_block = 0 <= self.loop_point < self.blocks.size

            if not (valid_len and valid_block):
                raise BrrException(f"Invalid loop point: {self.loop_point}")
