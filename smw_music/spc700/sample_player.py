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
from enum import Enum, auto
from pathlib import Path
from typing import Mapping

# Library imports
import pyaudio

from .brr import Brr, Envelope
from .nspc import set_pitch
from .spc700 import SAMPLE_FREQ

###############################################################################
# Private class definitions
###############################################################################


class _State(Enum):
    IDLE = auto()
    PLAYING = auto()
    KEYOFF = auto()
    PLAYOUT = auto()


###############################################################################
# API class definitions
###############################################################################


class SamplePlayer:
    _p: pyaudio.PyAudio
    _frames: deque[bytes]
    _state: _State

    ###########################################################################

    def __init__(self) -> None:
        # TODO: Add a .terminate on _p
        self._p = pyaudio.PyAudio()
        self._frames = deque()
        self._state = _State.IDLE

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
        if self._state == _State.PLAYING:
            self._state = _State.KEYOFF

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _play(
        self, brr: Brr, env: Envelope, tune: int, note: int, subnote: int
    ) -> None:
        self._state = _State.PLAYING

        # Arbitrary-ish size of the frame buffer we carry, there's nothing
        # special about the value.  Bigger means more audio after a sample is
        # released, so keep it low.
        buflen = 3

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
        ) as stream:
            for frame in brr.generate(pitch_reg, env):
                self._frames.append(bytes(frame))

                while len(self._frames) > buflen:
                    pass

                if self._state == _State.KEYOFF:
                    brr.keyoff()
                    self._state = _State.PLAYOUT

            # Wait for the output to drain
            while stream.is_active():
                pass

        self._state = _State.IDLE

    ###########################################################################

    def _start(
        self, brr: Brr, env: Envelope, tune: int, note: int, subnote: int
    ) -> None:
        # Busy loop if a new key comes when the last key was released but the
        # buffer isn't free
        while self._state in [_State.KEYOFF, _State.PLAYOUT]:
            pass

        if self._state == _State.IDLE:
            self._play(brr, env, tune, note, subnote)

    ###########################################################################

    def _stream_cb(
        self,
        in_data: bytes | None,
        frame_count: int,
        time_info: Mapping[str, float],
        status_flags: int,
    ) -> tuple[bytes, int]:
        while not len(self._frames) and self._state == _State.PLAYING:
            pass

        try:
            frame = self._frames.popleft()
            return (frame, pyaudio.paContinue)
        except IndexError:
            return (b"", pyaudio.paComplete)
