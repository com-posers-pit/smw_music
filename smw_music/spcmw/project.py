# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SPCMW Project settings."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from dataclasses import dataclass, field
from pathlib import Path

# Package imports
from smw_music.amk import BuiltinSampleGroup, BuiltinSampleSource
from smw_music.spcmw.echo import EchoConfig
from smw_music.spcmw.instrument import InstrumentConfig, InstrumentSample

###############################################################################
# API constant definitions
###############################################################################

EXTENSION = "spcmw"
N_BUILTIN_SAMPLES = 20

###############################################################################
# API class definitions
###############################################################################


@dataclass
class ProjectInfo:
    musicxml_fname: Path = Path("")
    project_name: str = ""
    composer: str = ""
    title: str = ""
    porter: str = ""
    game: str = ""

    ###########################################################################

    @property
    def is_valid(self) -> bool:
        return self.musicxml_fname.exists()


###############################################################################


@dataclass
class ProjectSettings:
    loop_analysis: bool = False
    superloop_analysis: bool = False
    measure_numbers: bool = True
    instruments: dict[str, InstrumentConfig] = field(
        default_factory=lambda: {}
    )
    global_volume: int = 128
    global_legato: bool = True
    echo: EchoConfig = field(
        default_factory=lambda: EchoConfig(
            set(), (0, 0), (False, False), 0, 0, False, 0
        )
    )
    start_measure: int = 1

    builtin_sample_group: BuiltinSampleGroup = BuiltinSampleGroup.OPTIMIZED
    builtin_sample_sources: list[BuiltinSampleSource] = field(
        default_factory=lambda: N_BUILTIN_SAMPLES
        * [BuiltinSampleSource.OPTIMIZED]
    )

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


###############################################################################


@dataclass
class Project:
    info: ProjectInfo | None = None
    settings: ProjectSettings = ProjectSettings()
