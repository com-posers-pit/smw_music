# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard UI state."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass, field
from pathlib import Path

# Library imports
from music21.pitch import Pitch

# Package imports
from smw_music import SmwMusicException
from smw_music.music_xml.echo import EchoConfig
from smw_music.music_xml.instrument import InstrumentConfig, InstrumentSample

###############################################################################
# API class definitions
###############################################################################


class NoSample(SmwMusicException):
    pass


###############################################################################


@dataclass
class PreferencesState:
    amk_fname: Path = Path("")
    spcplay_fname: Path = Path("")
    sample_pack_dname: Path = Path("")
    advanced_mode: bool = False
    dark_mode: bool = False
    release_check: bool = True


###############################################################################


@dataclass
class State:
    musicxml_fname: Path | None = None
    mml_fname: Path | None = None
    loop_analysis: bool = False
    superloop_analysis: bool = False
    measure_numbers: bool = True
    instruments: dict[str, InstrumentConfig] = field(
        default_factory=lambda: {}
    )
    global_volume: int = 128
    global_legato: bool = True
    global_echo_enable: bool = True
    echo: EchoConfig = field(
        default_factory=lambda: EchoConfig(
            set(), (0, 0), (False, False), 0, 0, False, 0
        )
    )
    unsaved: bool = True
    project_name: str | None = None
    porter: str = ""
    game: str = ""
    start_measure: int = 1

    sample_idx: tuple[str, str] | None = None

    unmapped: set[tuple[Pitch, str]] = field(default_factory=set)

    ###########################################################################
    # Property definitions
    ###########################################################################

    @property
    def sample(self) -> InstrumentSample:
        if self.sample_idx is None:
            raise NoSample()
        return self.samples[self.sample_idx]

    ###########################################################################

    @sample.setter
    def sample(self, sample: InstrumentSample) -> None:
        if self.sample_idx is not None:
            inst_name, sample_name = self.sample_idx
            inst = self.instruments[inst_name]
            if sample_name:
                inst.multisamples[sample_name] = sample
            else:
                inst.sample = sample

    ###########################################################################

    @property
    def samples(self) -> dict[tuple[str, str], InstrumentSample]:
        samples = {}

        for inst_name, inst in self.instruments.items():
            for sample_name, sample in inst.samples.items():
                samples[(inst_name, sample_name)] = sample

        return samples
