# SPDX-FileCopyrightText: 2024 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

###############################################################################
# Imports
###############################################################################

# Standard library imports
from functools import singledispatchmethod

# Package imports
from smw_music.song import Token
from smw_music.spcmw import Project

###############################################################################
# API class definitions
###############################################################################


class Exporter:
    project: Project

    ###########################################################################

    def __init__(self, project: Project) -> None:
        self.project = project
        self.directives: list[str] = []

    ###########################################################################

    def _append(self, directive: str) -> None:
        self.directives.append(directive)

    ###########################################################################

    # This needs to be included to keep mypy from complaining in subclasses
    @singledispatchmethod
    def emit(self, token: Token) -> None:
        raise NotImplementedError

    ###########################################################################

    def generate(self, tokens: list[Token]) -> None:
        for token in tokens:
            self.emit(token)
