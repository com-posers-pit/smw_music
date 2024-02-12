# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard save functionality."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
from pathlib import Path
from typing import TypedDict

# Library imports
import yaml

# Package imports
from smw_music.amk import (
    N_BUILTIN_SAMPLES,
    BuiltinSampleGroup,
    BuiltinSampleSource,
)

from .stypes import EchoDict, InstrumentDict, ProjectDict, SampleDict

###############################################################################
# Private constant definitions
###############################################################################

_CURRENT_SAVE_VERSION = 1

###############################################################################
# Private type definitions
###############################################################################


class _EchoDict(TypedDict):
    enables: list[int]
    vol_mag: list[float]
    vol_inv: list[bool]
    delay: int
    fb_mag: float
    fb_inv: bool
    fir_filt: int


###############################################################################


class _InstrumentDict(TypedDict):
    mute: bool
    solo: bool
    samples: dict[str, "_SampleDict"]


###############################################################################


class _SampleDict(TypedDict):
    octave_shift: int
    dynamics: dict[int, int]
    interpolate_dynamics: bool
    articulations: dict[int, list[int]]
    pan_enabled: bool
    pan_setting: int
    pan_l_invert: bool
    pan_r_invert: bool
    sample_source: int
    builtin_sample_index: int
    pack_sample: list[str]
    brr_fname: str
    adsr_mode: bool
    attack_setting: int
    decay_setting: int
    sus_level_setting: int
    sus_rate_setting: int
    gain_mode: int
    gain_setting: int
    tune_setting: int
    subtune_setting: int
    mute: bool
    solo: bool
    llim: str
    ulim: str
    notehead: str
    start: str
    track: bool


###############################################################################


class _SaveDict(TypedDict):
    tool_version: str
    save_version: int
    song: str
    time: str
    state: "_StateDict"


###############################################################################


class _StateDict(TypedDict):
    musicxml_fname: str | None
    mml_fname: str | None
    loop_analysis: bool
    measure_numbers: bool
    global_volume: bool
    global_legato: bool
    global_echo_enable: bool
    echo: _EchoDict
    instruments: dict[str, _InstrumentDict]
    porter: str
    game: str
    start_measure: int
    builtin_sample_group: int
    builtin_sample_sources: list[int]


###############################################################################
# Private function definitions
###############################################################################


def _load_echo(echo: _EchoDict) -> EchoDict:
    rv: EchoDict = {
        "vol_mag": echo["vol_mag"],
        "vol_inv": echo["vol_inv"],
        "delay": echo["delay"],
        "fb_mag": echo["fb_mag"],
        "fb_inv": echo["fb_inv"],
        "fir_filt": echo["fir_filt"],
    }

    return rv


###############################################################################


def _load_instrument(inst: _InstrumentDict) -> InstrumentDict:
    rv: InstrumentDict = {
        "mute": inst["mute"],
        "solo": inst["solo"],
        "samples": {k: _load_sample(v) for k, v in inst["samples"].items()},
    }

    return rv


###############################################################################


def _load_sample(sample: _SampleDict) -> SampleDict:
    rv: SampleDict = {
        "octave_shift": sample["octave_shift"],
        "dynamics": {
            "pppp": sample["dynamics"][0],
            "ppp": sample["dynamics"][1],
            "pp": sample["dynamics"][2],
            "p": sample["dynamics"][3],
            "mp": sample["dynamics"][4],
            "mf": sample["dynamics"][5],
            "f": sample["dynamics"][6],
            "ff": sample["dynamics"][7],
            "fff": sample["dynamics"][8],
            "ffff": sample["dynamics"][9],
        },
        "interpolate_dynamics": sample["interpolate_dynamics"],
        "articulations": sample["articulations"],
        "pan_enabled": sample["pan_enabled"],
        "pan_setting": sample["pan_setting"],
        "pan_l_invert": sample["pan_l_invert"],
        "pan_r_invert": sample["pan_r_invert"],
        "sample_source": sample["sample_source"],
        "builtin_sample_index": sample["builtin_sample_index"],
        "pack_sample": sample["pack_sample"],
        "brr_fname": sample["brr_fname"],
        "adsr_mode": sample["adsr_mode"],
        "attack_setting": sample["attack_setting"],
        "decay_setting": sample["decay_setting"],
        "sus_level_setting": sample["sus_level_setting"],
        "sus_rate_setting": sample["sus_rate_setting"],
        "gain_mode": sample["gain_mode"],
        "gain_setting": sample["gain_setting"],
        "tune_setting": sample["tune_setting"],
        "subtune_setting": sample["subtune_setting"],
        "mute": sample["mute"],
        "solo": sample["solo"],
        "llim": sample["ulim"],
        "ulim": sample["llim"],
        "notehead": sample["notehead"],
        "start": sample["start"],
        "track": sample.get("track", False),
    }

    return rv


###############################################################################
# API function definitions
###############################################################################


def load(fname: Path) -> ProjectDict:
    with open(fname, "r", encoding="utf8") as fobj:
        contents: _SaveDict = yaml.safe_load(fobj)

    assert contents["save_version"] == _CURRENT_SAVE_VERSION

    sdict = contents["state"]
    musicxml_fname: Path | str | None = sdict["musicxml_fname"]

    proj_dir = fname.parent.resolve()

    # Convert to absolute path if needed
    if musicxml_fname is not None:
        musicxml_fname = Path(musicxml_fname)
        if not musicxml_fname.is_absolute():
            musicxml_fname = proj_dir / musicxml_fname
    else:
        musicxml_fname = ""

    project: ProjectDict = {
        "tool_version": contents["tool_version"],
        "save_version": contents["save_version"],
        "time": contents["time"],
        "musicxml": str(musicxml_fname),
        "project_name": contents["song"],
        "composer": "",
        "title": "",
        "porter": sdict["porter"],
        "game": sdict["game"],
        "loop_analysis": sdict["loop_analysis"],
        "superloop_analysis": False,
        "measure_numbers": sdict["measure_numbers"],
        "global_volume": sdict["global_volume"],
        "global_legato": sdict["global_legato"],
        "global_echo": sdict["global_echo_enable"],
        "echo": _load_echo(sdict["echo"]),
        "instruments": {
            k: _load_instrument(v) for k, v in sdict["instruments"].items()
        },
        "builtin_sample_group": BuiltinSampleGroup.OPTIMIZED.value,
        "builtin_sample_sources": N_BUILTIN_SAMPLES
        * [BuiltinSampleSource.OPTIMIZED.value],
    }

    return project
