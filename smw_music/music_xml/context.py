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
class MmlState:  # pylint: disable=too-many-instance-attributes
    octave: int = 4
    default_note_len: int = 8
    grace: bool = False
    measure_numbers: bool = False
    slur: SlurState = SlurState.SLUR_IDLE
    tie: bool = False
    legato: bool = False
    accent: bool = False
    staccato: bool = False
    optimize_percussion: bool = False
    last_percussion: str = ""
