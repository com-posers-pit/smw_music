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
from smw_music.song import Song, Token
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
            info = project.info
            assert info is not None
            self.song = Song.from_music_xml(info.musicxml_fname)
        else:
            self.song = deepcopy(song)
        self.project = deepcopy(project)

    ###########################################################################

    def export(self) -> None:
        self.reduce()
        self.prepare()
        self.generate()
        self.finalize()

    ###########################################################################

    @classmethod
    def export_project(cls, project: Project) -> None:
        cls(project).export()

    ###########################################################################

    def finalize(self) -> None:
        pass

    ###########################################################################

    # This needs to be included to keep mypy from complaining in subclasses
    @singledispatchmethod
    def emit(self, token: Token) -> None:
        raise NotImplementedError

    ###########################################################################

    def generate(self, tokens: list[Token] | None = None) -> None:
        if tokens is None:
            tokens = self.song.tokens

        for token in tokens:
            self.emit(token)

    ###########################################################################

    def prepare(self) -> None:
        pass

    ###########################################################################

    def reduce(self) -> None:
        pass
