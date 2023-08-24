# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""
Tools for playing brr samples
"""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from collections import deque
from contextlib import closing
from pathlib import Path
from typing import Mapping

# Library imports
import pyaudio

from .brr import Brr, Envelope
from .nspc import set_pitch
from .spc700 import SAMPLE_FREQ

###############################################################################
# API class definitions
###############################################################################


class SamplePlayer:
    _p: pyaudio.PyAudio
    _frames: deque[bytes]

    ###########################################################################

    def __init__(self) -> None:
        self._running = False
        # TODO: Add a .terminate on _p
        self._p = pyaudio.PyAudio()
        self._frames = deque()

    ###########################################################################
    # API method definitions
    ###########################################################################

    def play_bin(
        self, binary: bytes, env: Envelope, tune: int, note: int, subnote: int
    ) -> None:
        self._start(Brr.from_binary(binary), env, tune, note, subnote)

    ###########################################################################

    def play_file(
        self, fname: Path, env: Envelope, tune: int, note: int, subnote: int
    ) -> None:
        self._start(Brr.from_file(fname), env, tune, note, subnote)

    ###########################################################################

    def stop(self) -> None:
        self._running = False

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _play(
        self, brr: Brr, env: Envelope, tune: int, note: int, subnote: int
    ) -> None:
        # Arbitrary-ish size of the frame buffer we carry, there's nothing
        # special about the value
        buflen = 10

        self._running = True
        self._frames.clear()

        pitch_reg = set_pitch(tune, note, subnote)

        with closing(
            pyaudio.PyAudio().open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_FREQ,
                output=True,
                frames_per_buffer=brr.SAMPLES_PER_FRAME,
                stream_callback=self._stream_cb,
            )
        ):
            for frame in brr.generate(pitch_reg, env):
                self._frames.append(bytes(frame))

                while self._running and len(self._frames) > buflen:
                    pass

                if not self._running:
                    break

    ###########################################################################

    def _start(
        self, brr: Brr, env: Envelope, tune: int, note: int, subnote: int
    ) -> None:
        if not self._running:
            self._play(brr, env, tune, note, subnote)

    ###########################################################################

    def _stream_cb(
        self,
        in_data: bytes | None,
        frame_count: int,
        time_info: Mapping[str, float],
        status_flags: int,
    ) -> tuple[bytes, int]:
        while not len(self._frames):
            if self._running:
                pass

        if self._running:
            frame = self._frames.popleft()
            return (frame, pyaudio.paContinue)
        else:
            return (b"", pyaudio.paAbort)
