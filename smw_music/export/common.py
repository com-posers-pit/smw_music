# SPDX-FileCopyrightText: 2024 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

###############################################################################
# Imports
###############################################################################

# Standard library imports
from copy import deepcopy
from functools import singledispatchmethod

# Package imports
from smw_music.common import SmwMusicException
from smw_music.song import (
    Dynamic,
    Instrument,
    Measure,
    Repeat,
    Song,
    Tempo,
    Token,
)
from smw_music.spcmw import Project

###############################################################################
# API class definitions
###############################################################################


class Exporter:
    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self, project: Project, song: Song | None = None) -> None:
        if song is None:
            musicxml = project.info.musicxml_fname
            if musicxml is None:
                raise SmwMusicException("MusicXML missing from project info")
            self.song = Song.from_music_xml(musicxml)
        else:
            self.song = deepcopy(song)
        self.project = deepcopy(project)

    ###########################################################################

    def export(self) -> None:
        pass

    ###########################################################################

    @classmethod
    def export_project(cls, project: Project) -> None:
        cls(project).export()

    ###########################################################################

    # This needs to be included to keep mypy from complaining in subclasses
    @singledispatchmethod
    def emit(self, token: Token) -> None:
        raise NotImplementedError

    ###########################################################################
    # Private function definitions
    ###########################################################################

    def _late_start(self) -> None:
        settings = self.project.settings
        start_measure = settings.start_measure

        if start_measure != 1:
            # If starting after the first measure, disable loop analysis
            # because things might be badly broken
            settings.loop_analysis = False
            settings.superloop_analysis = False

            for channel in self.song.channels:
                to_drop = start_measure - 1
                tokens: list[Token] = []
                for n, token in enumerate(channel):
                    if isinstance(
                        token, (Dynamic, Instrument, Measure, Tempo, Repeat)
                    ):
                        tokens.append(token)
                        if isinstance(token, Measure):
                            to_drop -= 1
                    if to_drop == 0:
                        tokens.extend(channel[n + 1 :])
                        break
                channel[:] = tokens
