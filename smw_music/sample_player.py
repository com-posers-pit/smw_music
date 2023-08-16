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

# Package imports
from smw_music.brr import Brr
from smw_music.nspc import set_pitch
from smw_music.spc700 import SAMPLE_FREQ

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
        self, binary: bytes, tune: int, note: int, subnote: int
    ) -> None:
        self._play(Brr.from_binary(binary), tune, note, subnote)

    ###########################################################################

    def play_file(
        self, fname: Path, tune: int, note: int, subnote: int
    ) -> None:
        self._play(Brr.from_file(fname), tune, note, subnote)

    ###########################################################################

    def stop(self) -> None:
        self._running = False

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _play(self, brr: Brr, tune: int, note: int, subnote: int) -> None:
        self._running = True
        self._frames.clear()

        fpb = brr.SAMPLES_PER_FRAME
        bpb = 2 * fpb
        pitch_reg = set_pitch(tune, note, subnote)

        with closing(
            pyaudio.PyAudio().open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_FREQ,
                output=True,
                frames_per_buffer=fpb,
                stream_callback=self._stream_cb,
            )
        ):
            working_frame = bytearray()
            for frame in brr.generate(pitch_reg):
                working_frame.extend(bytes(frame))

                while len(working_frame) > bpb:
                    self._frames.append(bytes(working_frame[:bpb]))
                    working_frame = working_frame[bpb:]

                while len(self._frames) > 10:
                    if not self._running:
                        break
                if not self._running:
                    break

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
