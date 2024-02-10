# SPDX-FileCopyrightText: 2024 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass, field
from functools import singledispatchmethod

# Package imports
from smw_music.song import Token
from smw_music.spcmw import Project

###############################################################################
# API class definitions
###############################################################################


@dataclass
class Exporter:
    project: Project
    directives: list[str] = field(default_factory=list, init=False)

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
