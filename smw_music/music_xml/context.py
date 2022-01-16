# SPDX-FileCopyrightText: 2021 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only


###############################################################################
# Standard Library imports
###############################################################################

from dataclasses import dataclass
from enum import auto, Enum

###############################################################################
# API class definitions
###############################################################################


class SlurState(Enum):
    SLUR_IDLE = auto()
    SLUR_ACTIVE = auto()
    SLUR_END = auto()


###############################################################################


@dataclass
class MmlState:
    octave: int
    default_note_len: int
    grace: bool = False
    measure_numbers: bool = False
    slur: SlurState = SlurState.SLUR_IDLE
    tie: bool = False
    legato: bool = False
    percussion: bool = False
