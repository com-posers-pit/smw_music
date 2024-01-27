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
from smw_music.amk import BuiltinSampleGroup, BuiltinSampleSource
from smw_music.music_xml.echo import EchoConfig
from smw_music.music_xml.instrument import InstrumentConfig, InstrumentSample
from smw_music.ui.utilization import Utilization, default_utilization

###############################################################################
# API constant definitions
###############################################################################

N_BUILTIN_SAMPLES = 20

###############################################################################
# API class definitions
###############################################################################


class NoSample(SmwMusicException):
    pass


###############################################################################


@dataclass
class ProjectSettingsState:
    musicxml_fname: Path
    project_name: str
    composer: str = ""
    title: str = ""
    porter: str = ""
    game: str = ""


###############################################################################


@dataclass
class State:
    project_settings: ProjectSettingsState | None = None
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
    start_measure: int = 1
    section_names: list[str] = field(default_factory=list)
    start_section_idx: int = 0

    unmapped: set[tuple[Pitch, str]] = field(default_factory=set)
    aram_util: Utilization = field(default_factory=default_utilization)
    aram_custom_sample_b: int = 0
    calculated_tune: tuple[float, tuple[int, float]] = (0, (0, 0))
    builtin_sample_group: BuiltinSampleGroup = BuiltinSampleGroup.OPTIMIZED
    builtin_sample_sources: list[BuiltinSampleSource] = field(
        default_factory=lambda: N_BUILTIN_SAMPLES
        * [BuiltinSampleSource.OPTIMIZED]
    )

    _sample_idx: tuple[str, str] | None = None

    ###########################################################################
    # Data model method definitions
    ###########################################################################

    def __post_init__(self) -> None:
        self._normalize_followers()
        self._normalize_sample_sources()

    ###########################################################################
    # Property definitions
    ###########################################################################

    @property
    def instrument(self) -> InstrumentConfig:
        return self.instruments[self.sample_idx[0]]

    ###########################################################################

    @property
    def loaded(self) -> bool:
        return self.project_settings is not None

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

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _normalize_followers(self) -> None:
        for inst in self.instruments.values():
            for sample in inst.multisamples.values():
                sample.track_settings(inst.sample)

    ###########################################################################

    def _normalize_sample_sources(self) -> None:
        # Use a short alias to the state variable
        sources = self.builtin_sample_sources
        nelem = len(self.builtin_sample_sources)

        match self.builtin_sample_group:
            case BuiltinSampleGroup.DEFAULT:
                sources[:] = nelem * [BuiltinSampleSource.DEFAULT]
            case BuiltinSampleGroup.OPTIMIZED:
                sources[:] = nelem * [BuiltinSampleSource.OPTIMIZED]
            case BuiltinSampleGroup.REDUX1:
                sources[:] = nelem * [BuiltinSampleSource.OPTIMIZED]
                sources[0x0D] = BuiltinSampleSource.EMPTY
                sources[0x0F] = BuiltinSampleSource.EMPTY
                sources[0x11] = BuiltinSampleSource.EMPTY
            case BuiltinSampleGroup.REDUX2:
                sources[:] = nelem * [BuiltinSampleSource.OPTIMIZED]
                sources[0x0D] = BuiltinSampleSource.EMPTY
                sources[0x0F] = BuiltinSampleSource.EMPTY
                sources[0x11] = BuiltinSampleSource.EMPTY
                sources[0x13] = BuiltinSampleSource.EMPTY
