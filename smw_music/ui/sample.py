#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
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
from typing import TextIO

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
    fname: str | None
    attack: int = 0
    decay: int = 0
    sustain: int = 0
    release: int = 0
    adsr_mode: bool = True
    gain_mode: GainMode = GainMode.DIRECT
    gain: int = 0
    tuning: int = 0
    subtuning: int = 0

    ###########################################################################

    @classmethod
    def from_regs(cls, fname: str, regs: list[int]) -> "Sample":
        tuning = regs[3]
        subtuning = regs[4]

        attack = 0xF & regs[0]
        decay = 0x7 & (regs[0] >> 4)
        adsr_mode = bool(regs[0] >> 7)
        sustain = regs[1] >> 5
        release = 0x1F & regs[1]

        gain = 0x1F & (regs[2])

        match (regs[2] >> 5):
            case 0b100:
                gain_mode = GainMode.DEC_LIN
            case 0b101:
                gain_mode = GainMode.DEC_EXP
            case 0b110:
                gain_mode = GainMode.INC_LIN
            case 0b111:
                gain_mode = GainMode.INC_BENT
            case _:  # 0b0xx
                gain_mode = GainMode.DIRECT
                gain = 0x7F & regs[2]

        return cls(
            fname,
            attack,
            decay,
            sustain,
            release,
            adsr_mode,
            gain_mode,
            gain,
            tuning,
            subtuning,
        )

    ###########################################################################

    @classmethod
    def from_pattern(cls, description: str) -> "Sample":
        # The '_' catches anything that comes before the opening '"'
        _, fname, param_str = description.split('"')
        param_str = param_str.strip()

        # Patterns apparently aren't rigorously defined, we can wind up with
        # extra spaces.  This removes them all, then splits on the '$', then
        # chucks the first one (which is empty because it comes before the
        # first '$'
        param_str = param_str.replace(" ", "")
        params = [int(x, 16) for x in param_str.split("$")[1:]]

        return cls.from_regs(fname, params[:5])

    ###########################################################################

    @classmethod
    def from_pattern_file(cls, fobj: TextIO) -> list["Sample"]:
        lines = fobj.readlines()
        return [cls.from_pattern(line) for line in lines if line.strip()]
