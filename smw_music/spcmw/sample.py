# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Wrapper for samples."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass, field
from functools import cached_property
from glob import iglob
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TextIO
from zipfile import ZipFile

# Package imports
from smw_music.spc700 import Brr, Envelope, GainMode

###############################################################################
# API Class Definitions
###############################################################################


@dataclass
class Sample:
    path: Path
    params: "SampleParams"
    data: bytes

    ###########################################################################

    @cached_property
    def brr(self) -> Brr:
        return Brr.from_binary(self.data)


###############################################################################


# This probably belongs in the AMK area
@dataclass
class SamplePack:
    path: Path

    ###########################################################################

    @property
    def samples(self) -> list[Sample]:
        return list(self._samples.values())

    ###########################################################################

    def __getitem__(self, key: Path) -> Sample:
        return self._samples[key]

    ###########################################################################

    def __post_init__(self) -> None:
        # Initialize the return value
        samples = {}

        # Unpack the pack zip file to a temporary directory
        with TemporaryDirectory() as tdir, ZipFile(self.path) as zobj:
            zobj.extractall(tdir)

            # Locate the pattern description files
            names = [Path(x) for x in zobj.namelist()]
            pat_files = [n for n in names if n.parts[-1] == "!patterns.txt"]

            for pat_file in pat_files:
                parent = pat_file.parents[0]
                parent_dir = tdir / parent
                sample_params = []
                with open(Path(tdir) / pat_file, "r", encoding="utf8") as fobj:
                    sample_params = SampleParams.from_pattern_file(fobj)

                # Stupid case insensitive file systems.  Build a map between
                # the lower-case version of file name in the directory and its
                brr_data = {}
                for fname in iglob("*.brr", root_dir=parent_dir):
                    with open(parent_dir / fname, "rb") as fobj:
                        brr_data[fname.lower()] = fobj.read()

                for brr_fname, params in sample_params:
                    try:
                        data = brr_data[brr_fname.lower()]
                        sample_file = parent / brr_fname
                        samples[sample_file] = Sample(
                            sample_file, params, data
                        )
                    except KeyError:
                        # If a file in the pattern file is missing, skip it
                        continue

            # Add brr files that aren't in the !patterns.txt file
            default_params = SampleParams.from_regs([0, 0, 0x7F, 0x10, 0])
            for fname in iglob("**/*.brr", root_dir=tdir, recursive=True):
                path = Path(fname)
                if path not in samples:
                    with open(Path(tdir) / fname, "rb") as fobj:
                        data = fobj.read()

                    samples[path] = Sample(path, default_params, data)

        self._samples = samples


###############################################################################


@dataclass
class SampleParams:
    envelope: Envelope = field(default_factory=Envelope)
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
            Envelope(
                adsr_mode,
                attack,
                decay,
                sustain_level,
                sustain_rate,
                gain_mode,
                gain,
            ),
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
        patterns = []
        for line in lines:
            line = line.split(";")[0].strip()
            if line:
                patterns.append(cls.from_pattern(line))

        return patterns
