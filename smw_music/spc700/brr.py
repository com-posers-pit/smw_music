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
# Imports
###############################################################################

# Standard library imports
import math
import wave
from collections.abc import Iterator, Sequence
from contextlib import suppress
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from struct import iter_unpack
from typing import List

# Library imports
import numpy as np
import numpy.typing as npt
from scipy.signal import find_peaks, lfilter, lfiltic  # type: ignore

# Package imports
from smw_music.common import SmwMusicException

from .nspc import calc_tune
from .spc700 import PITCH_REG_SCALE, SAMPLE_FREQ, Envelope

###############################################################################
# API constant definitions
###############################################################################

BLOCK_SIZE = 9

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


def _block_loops(block: Sequence[int]) -> bool:
    return bool(block[0] & 0x2)


###############################################################################


def _end_block(block: Sequence[int]) -> bool:
    return bool(block[0] & 0x1)


###############################################################################


def _u4_to_s4(data: npt.NDArray[np.uint8]) -> npt.NDArray[np.int8]:
    return (0xF & (data.astype(np.int8) + 8)) - 8


###############################################################################
# API function definitions
###############################################################################


def extract_brrs(spc: bytes) -> List["Brr"]:
    header = spc[:256]
    aram = spc[256:]

    magic = header[:0x23]

    if magic != b"SNES-SPC700 Sound File Data v0.30\x1A\x1A":
        return []
    if len(spc) < 0x10200:
        return []

    dir_reg = spc[0x1015D]
    sample_dir_offset = 256 * dir_reg
    sample_dir = aram[sample_dir_offset : sample_dir_offset + 0x400]

    brrs = []
    for start_addr, loop in iter_unpack("<2H", sample_dir):
        brr = bytearray()

        last_addr = addr = start_addr
        valid_sample = False

        while addr < len(aram):
            if addr >= 0x10000:
                break
            if last_addr < sample_dir_offset <= addr:
                break

            block = aram[addr : addr + BLOCK_SIZE]
            addr += BLOCK_SIZE

            brr.extend(block)

            if _end_block(block):
                valid_sample = True
                sample_loops = _block_loops(block)
                break

        if valid_sample:
            loop_offset = 0
            if sample_loops:
                loop_offset = loop - start_addr

            if loop_offset < 0:
                continue

            brr = bytearray(loop_offset.to_bytes(2, "little")) + brr
            with suppress(BrrException):
                brrs.append(Brr.from_binary(brr))

    return brrs


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
    samples_per_frame: int = 1024
    _waveform_cache: dict[int, npt.NDArray[np.int16]] = field(
        init=False, repr=False, compare=False, default_factory=dict
    )
    _keyed: bool = False

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

    def generate(
        self, pitch_reg: int, env: Envelope
    ) -> Iterator[npt.NDArray[np.int16]]:
        self._keyed = True

        # Variable initialization
        proc = np.zeros(SAMPLES_PER_BLOCK)
        chunk_size = self.samples_per_frame / SAMPLES_PER_BLOCK

        dt = pitch_reg / PITCH_REG_SCALE

        # Loop the requested number of times, starting at block 0 the first
        # time and at the loop block all other times
        start_block = 0
        idx = 0

        env_times, envelope = env.envelope
        env_times *= SAMPLE_FREQ

        buffer = np.zeros(SAMPLES_PER_BLOCK, dtype=np.int16)
        weights = np.zeros(self.samples_per_frame)
        nblocks = int(np.ceil(chunk_size * dt))
        frame_size = 1 + nblocks * SAMPLES_PER_BLOCK
        frame = np.zeros(frame_size)
        xp = np.array([-1])
        ts = np.array([-dt])

        one_shot = not self.sample_loops
        done = False

        # TODO: refactor with generate_waveform
        while True:
            for n in range(start_block, self.nblocks):
                if idx == 0:
                    frame[0] = frame[-1]
                    xp = xp[-1] + np.arange(len(frame))
                    ts = np.arange(ts[-1] + dt, xp[-1], dt)

                # Get the filter coefficients
                a_coeffs = _FILTERS[self.filters[n]]
                b_coeffs = [2 ** self.ranges[n]]

                # Run the IIR filter
                init = lfiltic(b_coeffs, a_coeffs, [proc[-1], proc[-2]])
                proc, _ = lfilter(b_coeffs, a_coeffs, self.samples[n], zi=init)

                frame[
                    1
                    + idx * SAMPLES_PER_BLOCK : 1
                    + (idx + 1) * SAMPLES_PER_BLOCK
                ] = proc

                idx += 1

                emit = False
                if (n == self.nblocks - 1) and one_shot:
                    frame[1 + idx * SAMPLES_PER_BLOCK :] = 0
                    emit = True

                if idx == nblocks:
                    idx = 0
                    emit = True

                if emit:
                    if self._keyed:
                        weights = np.interp(ts, env_times, envelope)
                    else:
                        weights = weights[-1] * np.ones(len(ts))
                        weights -= 8 * np.arange(len(ts)) / 2**11
                        weights = np.maximum(weights, 0)
                        done = True

                    result = np.interp(ts, xp, frame)
                    result = np.round(result * weights).astype(np.int16)
                    buffer = np.hstack((buffer, result))

                    while len(buffer) >= self.samples_per_frame:
                        yield buffer[: self.samples_per_frame]
                        buffer = buffer[self.samples_per_frame :]

                    if one_shot or done:
                        rv = np.zeros(self.samples_per_frame, dtype=np.int16)
                        rv[: len(buffer)] = buffer[:]
                        yield rv
                        return

            start_block = self.loop_block

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

    def keyoff(self) -> None:
        self._keyed = False

    ###########################################################################

    def to_wav(
        self, fname: str, loops: int = 0, framerate: int = SAMPLE_FREQ
    ) -> None:
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
        return calc_tune(fundamental, note, target)

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
        for n, (rval, fval, samples) in enumerate(
            zip(self.ranges, self.filters, self.samples)
        ):
            block = self.blocks[n]
            loops = _block_loops(block)
            ends = _end_block(block)
            data = [rval, fval, loops, ends, *samples]
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
        # Remove any DC bias
        waveform = np.array(self.generate_waveform(loops), dtype=np.double)
        waveform -= waveform.mean()

        spec = np.abs(np.fft.rfft(waveform[start:]))
        spec /= spec.max()
        peak: float
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

        rv = np.empty((evens.shape[0], 16), dtype=np.uint8)
        rv[:, ::2] = evens
        rv[:, 1::2] = odds

        return _u4_to_s4(rv)

    ###########################################################################
    # Data model methods
    ###########################################################################

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.binary == other.binary
        return False

    ###########################################################################

    def __hash__(self) -> int:
        return hash(self.binary)

    ###########################################################################

    def __post_init__(self) -> None:
        if self.sample_loops and self.loop_point is not None:
            valid_len = self.loop_point % BLOCK_SIZE == 0
            valid_block = 0 <= self.loop_point < self.blocks.size

            if not (valid_len and valid_block):
                raise BrrException(f"Invalid loop point: {self.loop_point}")
