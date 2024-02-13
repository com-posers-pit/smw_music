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

_CURRENT_SAVE_VERSION = 0

###############################################################################
# Private type definitions
###############################################################################


class _EchoDict_v0(TypedDict):
    enables: list[int]
    vol_mag: list[float]
    vol_inv: list[bool]
    delay: int
    fb_mag: float
    fb_inv: bool
    fir_filt: int


###############################################################################


class _InstrumentDict_v0(TypedDict):
    name: str
    octave: int
    transpose: int
    dynamics: dict[int, int]
    dynamics_present: list[int]
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


###############################################################################


class _SaveDict_v0(TypedDict):
    tool_version: str
    save_version: int
    song: str
    time: str
    state: "_StateDict_v0"


###############################################################################


class _StateDict_v0(TypedDict):
    musicxml_fname: str
    mml_fname: str
    loop_analysis: bool
    measure_numbers: bool
    instrument_idx: int
    global_volume: bool
    global_legato: bool
    global_echo_enable: bool
    echo: _EchoDict_v0
    instruments: list[_InstrumentDict_v0]
    porter: str
    game: str
    start_measure: int


###############################################################################
# Private function definitions
###############################################################################


def _load_echo_v0(echo: _EchoDict_v0) -> EchoDict:
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


def _load_instrument_v0(inst: _InstrumentDict_v0) -> InstrumentDict:
    rv: InstrumentDict = {
        "mute": inst["mute"],
        "solo": inst["solo"],
        "samples": {"": _load_sample_v0(inst)},
    }

    return rv


###############################################################################


def _load_sample_v0(inst: _InstrumentDict_v0) -> SampleDict:
    sample: SampleDict = {
        "octave_shift": inst["octave"],
        "dynamics": {
            "pppp": inst["dynamics"][0],
            "ppp": inst["dynamics"][1],
            "pp": inst["dynamics"][2],
            "p": inst["dynamics"][3],
            "mp": inst["dynamics"][4],
            "mf": inst["dynamics"][5],
            "f": inst["dynamics"][6],
            "ff": inst["dynamics"][7],
            "fff": inst["dynamics"][8],
            "ffff": inst["dynamics"][9],
        },
        "interpolate_dynamics": inst["interpolate_dynamics"],
        "articulations": inst["articulations"],
        "pan_enabled": inst["pan_enabled"],
        "pan_setting": inst["pan_setting"],
        "pan_l_invert": inst["pan_l_invert"],
        "pan_r_invert": inst["pan_r_invert"],
        "sample_source": inst["sample_source"],
        "builtin_sample_index": inst["builtin_sample_index"],
        "pack_sample": inst["pack_sample"],
        "brr_fname": inst["brr_fname"],
        "adsr_mode": inst["adsr_mode"],
        "attack_setting": inst["attack_setting"],
        "decay_setting": inst["decay_setting"],
        "sus_level_setting": inst["sus_level_setting"],
        "sus_rate_setting": inst["sus_rate_setting"],
        "gain_mode": inst["gain_mode"],
        "gain_setting": inst["gain_setting"],
        "tune_setting": inst["tune_setting"],
        "subtune_setting": inst["subtune_setting"],
        "mute": inst["mute"],
        "solo": inst["solo"],
        "llim": "A0",
        "ulim": "C7",
        "notehead": "normal",
        "start": "A0",
        "track": False,
    }

    return sample


###############################################################################
# API function definitions
###############################################################################


def load_v0(fname: Path) -> ProjectDict:
    with open(fname, "r", encoding="utf8") as fobj:
        contents: _SaveDict_v0 = yaml.safe_load(fobj)

    assert contents["save_version"] == _CURRENT_SAVE_VERSION

    sdict = contents["state"]
    if param_fname := sdict["musicxml_fname"]:
        musicxml_fname = str(Path(param_fname).resolve())
    else:
        musicxml_fname = ""

    project: ProjectDict = {
        "tool_version": contents["tool_version"],
        "save_version": contents["save_version"],
        "time": contents["time"],
        "musicxml": musicxml_fname,
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
        "echo": _load_echo_v0(sdict["echo"]),
        "instruments": {
            inst["name"]: _load_instrument_v0(inst)
            for inst in sdict["instruments"]
        },
        "builtin_sample_group": BuiltinSampleGroup.OPTIMIZED.value,
        "builtin_sample_sources": N_BUILTIN_SAMPLES
        * [BuiltinSampleSource.OPTIMIZED.value],
    }

    return project
