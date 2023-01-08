#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Wrapper for samples."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass
from enum import IntEnum, auto
from pathlib import Path

###############################################################################
# API Class Definitions
###############################################################################


class GainMode(IntEnum):
    DIRECT = auto()
    INC_LIN = auto()
    INC_BENT = auto()
    DEC_LIN = auto()
    DEC_EXP = auto()


###############################################################################


@dataclass
class Sample:
    fname: Path
    attack: int = 0
    decay: int = 0
    sustain: int = 0
    release: int = 0
    adsr_mode: bool = True
    gain_mode: GainMode = GainMode.DIRECT
    gain: int = 0
    tuning: int = 0
    subtuning: int = 0
