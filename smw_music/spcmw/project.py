# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SPCMW Project settings."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Library imports
import yaml

# Package imports
from smw_music import __version__
from smw_music.amk import (
    N_BUILTIN_SAMPLES,
    BuiltinSampleGroup,
    BuiltinSampleSource,
)
from smw_music.spc700 import EchoConfig

from .instrument import InstrumentConfig, InstrumentSample
from .stypes import EchoDict, InstrumentDict, ProjectDict, SampleDict

###############################################################################
# API constant definitions
###############################################################################

CURRENT_SAVE_VERSION = 2
EXTENSION = "spcmw"


###############################################################################
# Private function definitions
###############################################################################


def _save_echo(echo: EchoConfig) -> EchoDict:
    return {
        "vol_mag": list(echo.vol_mag),
        "vol_inv": list(echo.vol_inv),
        "delay": echo.delay,
        "fb_mag": echo.fb_mag,
        "fb_inv": echo.fb_inv,
        "fir_filt": echo.fir_filt,
    }


###############################################################################


def _save_instrument(inst: InstrumentConfig) -> InstrumentDict:
    return {
        "mute": inst.mute,
        "solo": inst.solo,
        "samples": {k: _save_sample(v) for k, v in inst.samples.items()},
    }


###############################################################################


def _save_sample(sample: InstrumentSample) -> SampleDict:
    return {
        "octave_shift": sample.octave_shift,
        "dynamics": {k.value: v for k, v in sample.dynamics.items()},
        "interpolate_dynamics": sample.dyn_interpolate,
        "articulations": {
            k.value: [v.length, v.volume] for k, v in sample.artics.items()
        },
        "pan_enabled": sample.pan_enabled,
        "pan_setting": sample.pan_setting,
        "pan_l_invert": sample.pan_invert[0],
        "pan_r_invert": sample.pan_invert[1],
        "sample_source": sample.sample_source.value,
        "builtin_sample_index": sample.builtin_sample_index,
        "pack_sample": [sample.pack_sample[0], str(sample.pack_sample[1])],
        "brr_fname": str(sample.brr_fname),
        "adsr_mode": sample.envelope.adsr_mode,
        "attack_setting": sample.envelope.attack_setting,
        "decay_setting": sample.envelope.decay_setting,
        "sus_level_setting": sample.envelope.sus_level_setting,
        "sus_rate_setting": sample.envelope.sus_rate_setting,
        "gain_mode": sample.envelope.gain_mode.value,
        "gain_setting": sample.envelope.gain_setting,
        "tune_setting": sample.tune_setting,
        "subtune_setting": sample.subtune_setting,
        "mute": sample.mute,
        "solo": sample.solo,
        "ulim": str(sample.ulim),
        "llim": str(sample.llim),
        "notehead": str(sample.notehead),
        "start": str(sample.start),
        "track": bool(sample.track),
    }


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
            (0, 0), (False, False), 0, 0, False, 0
        )
    )
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
    settings: ProjectSettings = field(default_factory=ProjectSettings)

    ###########################################################################

    def save(self, fname: Path) -> None:
        proj_dir = fname.parent.resolve()
        info = ProjectInfo() if self.info is None else self.info
        settings = self.settings
        musicxml = info.musicxml_fname
        if musicxml:
            musicxml = musicxml.resolve()
            with suppress(ValueError):
                musicxml = musicxml.relative_to(proj_dir)

        contents: ProjectDict = {
            # Meta info
            "tool_version": __version__,
            "save_version": CURRENT_SAVE_VERSION,
            "time": f"{datetime.utcnow()}",
            # ProjectInfo
            "musicxml": str(musicxml),
            "project_name": info.project_name,
            "composer": info.composer,
            "title": info.title,
            "porter": info.porter,
            "game": info.game,
            # ProjectSettings
            "loop_analysis": settings.loop_analysis,
            "superloop_analysis": settings.superloop_analysis,
            "measure_numbers": settings.measure_numbers,
            "global_volume": settings.global_volume,
            "global_legato": settings.global_legato,
            "echo": _save_echo(settings.echo),
            "instruments": {
                k: _save_instrument(v) for k, v in settings.instruments.items()
            },
            "builtin_sample_group": settings.builtin_sample_group.value,
            "builtin_sample_sources": [
                x.value for x in settings.builtin_sample_sources
            ],
        }

        with open(fname, "w", encoding="utf8") as fobj:
            yaml.safe_dump(contents, fobj)
