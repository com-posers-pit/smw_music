# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SPCMW Project settings."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass
from pathlib import Path

###############################################################################
# API constant definitions
###############################################################################

EXTENSION = "spcmw"

###############################################################################
# API class definitions
###############################################################################


@dataclass
class ProjectInfo:
    musicxml_fname: Path = Path("")
    project_name: str = ""
    composer: str = ""
    title: str = ""
    porter: str = ""
    game: str = ""

    ###########################################################################

    @property
    def is_valid(self) -> bool:
        return self.musicxml_fname.exists()


###############################################################################

###############################################################################
# API function definitions
###############################################################################
