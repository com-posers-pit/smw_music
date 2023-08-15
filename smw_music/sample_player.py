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
from contextlib import closing, suppress
from pathlib import Path
from threading import Thread

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
    def __init__(self):
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

        pitch_reg = set_pitch(tune, note, subnote)
        th = Thread(target=self._play_frames, daemon=True)

        started = False
        for frame in brr.generate(pitch_reg):
            self._frames.append(frame)
            while len(self._frames) > 1000:
                if not self._running:
                    break
            if not self._running:
                break
            if not started:
                started = True
                th.start()

    ###########################################################################

    def _play_frames(self) -> None:
        with closing(
            pyaudio.PyAudio().open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_FREQ,
                output=True,
            )
        ) as stream:
            with suppress(IndexError):
                while True:
                    stream.write(self._frames.popleft())
                    if not self._running:
                        break
