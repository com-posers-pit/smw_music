# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Wrapper for samples."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TextIO
from zipfile import ZipFile

# Package imports
from smw_music.ui.state import GainMode

###############################################################################
# API Function Definitions
###############################################################################


def extract_sample_pack(
    pack_file: Path,
) -> dict[tuple[str, ...], "SampleParams"]:
    # Initialize the return value
    patterns = {}

    # Unpack the pack zip file to a temporary directory
    with TemporaryDirectory() as tdir, ZipFile(pack_file) as zobj:
        zobj.extractall(tdir)

        # Locate the pattern description files
        names = [Path(x) for x in zobj.namelist()]
        pat_files = [n for n in names if n.parts[-1] == "!patterns.txt"]

        for pat_file in pat_files:
            parent = pat_file.parents[0].parts
            samples = []
            with open(Path(tdir) / pat_file, "r", encoding="utf8") as fobj:
                samples = SampleParams.from_pattern_file(fobj)

            for fname, params in samples:
                patterns[parent + (fname,)] = params

    return patterns


###############################################################################
# API Class Definitions
###############################################################################


@dataclass
class SampleParams:
    attack: int = 0
    decay: int = 0
    sustain_level: int = 0
    sustain_rate: int = 0
    adsr_mode: bool = True
    gain_mode: GainMode = GainMode.DIRECT
    gain: int = 0
    tuning: int = 0
    subtuning: int = 0

    ###########################################################################
    # Constructor definitions
    ###########################################################################

    @classmethod
    def from_regs(cls, regs: list[int]) -> "SampleParams":
        tuning = regs[3]
        subtuning = regs[4]

        attack = 0xF & regs[0]
        decay = 0x7 & (regs[0] >> 4)
        adsr_mode = bool(regs[0] >> 7)
        sustain_level = regs[1] >> 5
        sustain_rate = 0x1F & regs[1]

        gain = 0x1F & (regs[2])

        match (regs[2] >> 5):
            case 0b100:
                gain_mode = GainMode.DECLIN
            case 0b101:
                gain_mode = GainMode.DECEXP
            case 0b110:
                gain_mode = GainMode.INCLIN
            case 0b111:
                gain_mode = GainMode.INCBENT
            case _:  # 0b0xx
                gain_mode = GainMode.DIRECT
                gain = 0x7F & regs[2]

        return cls(
            attack,
            decay,
            sustain_level,
            sustain_rate,
            adsr_mode,
            gain_mode,
            gain,
            tuning,
            subtuning,
        )

    ###########################################################################

    @classmethod
    def from_pattern(cls, description: str) -> tuple[str, "SampleParams"]:
        # The '_' catches anything that comes before the opening '"'
        _, fname, param_str = description.split('"')
        param_str = param_str.strip()

        # Patterns apparently aren't rigorously defined, we can wind up with
        # extra spaces.  This removes them all, then splits on the '$', then
        # chucks the first one (which is empty because it comes before the
        # first '$'
        param_str = param_str.replace(" ", "")
        params = [int(x, 16) for x in param_str.split("$")[1:]]

        return (fname, cls.from_regs(params[:5]))

    ###########################################################################

    @classmethod
    def from_pattern_file(
        cls, fobj: TextIO
    ) -> list[tuple[str, "SampleParams"]]:
        lines = fobj.readlines()
        return [cls.from_pattern(line) for line in lines if line.strip()]
