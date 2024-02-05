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

# Library imports
from music21.pitch import Pitch

# Package imports
from smw_music import SmwMusicException
from smw_music.amk import Utilization, default_utilization
from smw_music.music_xml.instrument import InstrumentConfig, InstrumentSample
from smw_music.spcmw import Project

###############################################################################
# API class definitions
###############################################################################


class NoSample(SmwMusicException):
    pass


###############################################################################


@dataclass
class State:
    project: Project = Project()
    unsaved: bool = True
    section_names: list[str] = field(default_factory=list)
    start_section_idx: int = 0

    unmapped: set[tuple[Pitch, str]] = field(default_factory=set)
    aram_util: Utilization = field(default_factory=default_utilization)
    aram_custom_sample_b: int = 0
    calculated_tune: tuple[float, tuple[int, float]] = (0, (0, 0))

    _sample_idx: tuple[str, str] | None = None

    ###########################################################################
    # Property definitions
    ###########################################################################

    @property
    def instrument(self) -> InstrumentConfig:
        return self.instruments[self.sample_idx[0]]

    ###########################################################################

    @property
    def loaded(self) -> bool:
        return self.info is not None

    ###########################################################################

    @property
    def sample(self) -> InstrumentSample:
        return self.samples[self.sample_idx]

    ###########################################################################

    @sample.setter
    def sample(self, sample: InstrumentSample) -> None:
        inst_name, sample_name = self.sample_idx
        inst = self.instruments[inst_name]
        if sample_name:
            inst.multisamples[sample_name] = sample
        else:
            inst.sample = sample

    ###########################################################################

    @property
    def sample_idx(self) -> tuple[str, str]:
        if self._sample_idx is None:
            raise NoSample()
        return self._sample_idx

    ###########################################################################

    @sample_idx.setter
    def sample_idx(self, sample_idx: tuple[str, str]) -> None:
        self._sample_idx = sample_idx

    ###########################################################################

    @property
    def samples(self) -> dict[tuple[str, str], InstrumentSample]:
        samples = {}

        for inst_name, inst in self.instruments.items():
            for sample_name, sample in inst.samples.items():
                samples[(inst_name, sample_name)] = sample

        return samples
