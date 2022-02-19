# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only


###############################################################################
# Standard Library imports
###############################################################################

from dataclasses import dataclass, field
from typing import Optional

###############################################################################
# API variable definitions
###############################################################################

# Default dynamics mapping
DEFAULT_DYN = {
    "PPPP": 26,
    "PPP": 38,
    "PP": 64,
    "P": 90,
    "MP": 115,
    "MF": 141,
    "F": 179,
    "FF": 217,
    "FFF": 230,
    "FFFF": 245,
}

###############################################################################

DEFAULT_QUANT = {
    "DEF": 0x7A,
    "STAC": 0x5A,
    "ACC": 0x7F,
    "ACCSTAC": 0x5F,
}

###############################################################################
# API function definitions
###############################################################################


def inst_from_name(name: str) -> int:
    # Default instrument mapping, from Wakana's tutorial
    inst_map = {
        "flute": 0,
        "marimba": 3,
        "cello": 4,
        "trumpet": 6,
        "bass": 8,
        "bassguitar": 8,
        "electricbass": 8,
        "piano": 13,
        "guitar": 17,
        "electricguitar": 17,
    }

    return inst_map.get(name.lower(), 0)


###############################################################################
# API class definitions
###############################################################################


@dataclass
class InstrumentConfig:
    name: str
    instrument: int = 0
    octave: int = 3
    dynamics: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_DYN))
    dynamics_present: set[str] = field(default_factory=set)
    quant: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_QUANT))
    pan: Optional[int] = None
