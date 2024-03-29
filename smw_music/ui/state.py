# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard UI state."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass, field, replace
from functools import cached_property
from typing import cast

# Library imports
from music21.pitch import Pitch

# Package imports
from smw_music.common import SmwMusicException
from smw_music.ext_tools.amk import Utilization, default_utilization
from smw_music.spcmw import InstrumentConfig, InstrumentSample, Project

###############################################################################
# API class definitions
###############################################################################


class NoProject(SmwMusicException):
    pass


###############################################################################


class NoSample(SmwMusicException):
    pass


###############################################################################


@dataclass(frozen=True)
class State:
    _project: Project | None = None
    start_measure: int = 1
    start_section_idx: int = 0

    unmapped: set[tuple[Pitch, str]] = field(default_factory=set)
    aram_util: Utilization = field(default_factory=default_utilization)
    aram_custom_sample_b: int = 0
    calculated_tune: tuple[float, tuple[int, float]] = (0, (0, 0))
    section_names: list[str] = field(default_factory=list)

    _sample_idx: tuple[str, str] | None = None

    ###########################################################################
    # API function definitions
    ###########################################################################

    def replace_instrument(self, instrument: InstrumentConfig) -> "State":
        inst_name, _ = self.sample_idx

        instruments = self.project.settings.instruments.copy()
        instruments[inst_name] = instrument

        settings = replace(self.project.settings, instruments=instruments)
        project = replace(self.project, settings=settings)
        return replace(self, _project=project)

    ###########################################################################

    def replace_sample(self, sample: InstrumentSample) -> "State":
        inst_name, sample_name = self.sample_idx

        inst = self.project.settings.instruments[inst_name]

        if sample_name:
            # Multisample
            multisamples = inst.multisamples.copy()
            multisamples[sample_name] = sample
            instrument = replace(inst, multisamples=multisamples)
        else:
            # Top-level instrument
            instrument = replace(inst, sample=sample)

        return self.replace_instrument(instrument)

    ###########################################################################
    # Property definitions
    ###########################################################################

    @property
    def instrument(self) -> InstrumentConfig:
        return self.project.settings.instruments[self.sample_idx[0]]

    ###########################################################################

    @property
    def loaded(self) -> bool:
        return self._project is not None

    ###########################################################################

    @property
    def project(self) -> Project:
        if self.loaded:
            return cast(Project, self._project)
        raise NoProject()

    ###########################################################################

    @property
    def sample(self) -> InstrumentSample:
        return self.samples[self.sample_idx]

    ###########################################################################

    @property
    def sample_idx(self) -> tuple[str, str]:
        if self._sample_idx is None:
            raise NoSample()
        return self._sample_idx

    ###########################################################################

    @cached_property
    def samples(self) -> dict[tuple[str, str], InstrumentSample]:
        samples = {}

        for inst_name, inst in self.project.settings.instruments.items():
            for sample_name, sample in inst.samples.items():
                samples[(inst_name, sample_name)] = sample

        return samples
