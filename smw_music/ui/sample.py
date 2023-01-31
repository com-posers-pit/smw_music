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
from typing import TextIO

###############################################################################
# API Function Definitions
###############################################################################


def attack_dn2eu(setting: int) -> str:
    return [
        "4.1s",
        "2.6s",
        "1.5s",
        "1.0s",
        "640ms",
        "380ms",
        "260ms",
        "160ms",
        "96ms",
        "64ms",
        "40ms",
        "24ms",
        "16ms",
        "10ms",
        "6ms",
        "0ms",
    ][setting]


###############################################################################


def decay_dn2eu(setting: int) -> str:
    return [
        "1.2s",
        "740ms",
        "440ms",
        "290ms",
        "180ms",
        "110ms",
        "74ms",
        "37ms",
    ][setting]


###############################################################################


def gain_inclin_dn2eu(setting: int) -> str:
    return [
        "Inf",
        "4.1s",
        "3.1s",
        "2.6s",
        "2.0s",
        "1.5s",
        "1.3s",
        "1.0s",
        "770ms",
        "640ms",
        "510ms",
        "380ms",
        "320ms",
        "260ms",
        "190ms",
        "160ms",
        "130ms",
        "96ms",
        "80ms",
        "64ms",
        "48ms",
        "40ms",
        "32ms",
        "24ms",
        "20ms",
        "16ms",
        "12ms",
        "10ms",
        "8ms",
        "6ms",
        "4ms",
        "2ms",
    ][setting]


###############################################################################


def sus_level_dn2eu(setting: int) -> str:
    return ["1/8", "2/8", "3/8", "4/8", "5/8", "6/8", "7/8", "1"][setting]


###############################################################################


def sus_rate_dn2eu(setting: int) -> str:
    return [
        "Inf",
        "38s",
        "28s",
        "24s",
        "19s",
        "14s",
        "12s",
        "9.4s",
        "7.1s",
        "5.9s",
        "4.7s",
        "3.5s",
        "2.9s",
        "2.4s",
        "1.8s",
        "1.5s",
        "1.2s",
        "880ms",
        "740ms",
        "590ms",
        "440ms",
        "370ms",
        "290ms",
        "220ms",
        "180ms",
        "150ms",
        "110ms",
        "92ms",
        "74ms",
        "55ms",
        "37ms",
        "18ms",
    ][setting]


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
    # Constructor definitions
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
