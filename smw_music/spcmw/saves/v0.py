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
from typing import NotRequired, TypedDict

# Library imports
import yaml

from .. import stypes as v2
from . import v1

###############################################################################
# API type definitions
###############################################################################


class InstrumentDict(TypedDict):
    name: str
    octave: int
    transpose: int
    dynamics: dict[int, int]
    dynamics_present: list[int]
    interpolate_dynamics: bool
    articulations: dict[int, list[int]]
    pan_enabled: bool
    pan_setting: int
    pan_l_invert: NotRequired[bool]
    pan_r_invert: NotRequired[bool]
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


class SaveDict(TypedDict):
    tool_version: str
    save_version: int
    song: str
    time: str
    state: "StateDict"


###############################################################################


class StateDict(TypedDict):
    musicxml_fname: str
    mml_fname: str
    loop_analysis: bool
    measure_numbers: bool
    instrument_idx: int
    global_volume: bool
    global_legato: bool
    global_echo_enable: bool
    echo: v1.EchoDict
    instruments: list[InstrumentDict]
    porter: str
    game: str
    start_measure: NotRequired[int]


###############################################################################
# Private function definitions
###############################################################################


def _load_instrument(inst: InstrumentDict) -> v1.InstrumentDict:
    rv: v1.InstrumentDict = {
        "mute": inst["mute"],
        "solo": inst["solo"],
        "samples": {"": _load_sample(inst)},
    }

    return rv


###############################################################################


def _load_sample(inst: InstrumentDict) -> v1.SampleDict:
    sample: v1.SampleDict = {
        "octave_shift": inst["octave"],
        "dynamics": {n: inst["dynamics"][n] for n in range(10)},
        "interpolate_dynamics": inst["interpolate_dynamics"],
        "articulations": inst["articulations"],
        "pan_enabled": inst["pan_enabled"],
        "pan_setting": inst["pan_setting"],
        "pan_l_invert": inst.get("pan_l_invert", False),
        "pan_r_invert": inst.get("pan_r_invert", False),
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


def to_v1(fname: Path, contents: SaveDict) -> v1.SaveDict:
    sdict = contents["state"]
    if param_fname := sdict["musicxml_fname"]:
        musicxml_fname = str(Path(param_fname).resolve())
    else:
        musicxml_fname = None
    if param_fname := sdict["mml_fname"]:
        mml_fname = str(Path(param_fname).resolve())
    else:
        mml_fname = None

    project: v1.SaveDict = {
        "tool_version": contents["tool_version"],
        "save_version": 1,  # Override
        "song": contents["song"],
        "time": contents["time"],
        "state": {
            "musicxml_fname": musicxml_fname,
            "mml_fname": mml_fname,
            "loop_analysis": sdict["loop_analysis"],
            "measure_numbers": sdict["measure_numbers"],
            "global_volume": sdict["global_volume"],
            "global_legato": sdict["global_legato"],
            "global_echo_enable": sdict["global_echo_enable"],
            "echo": sdict["echo"],
            "instruments": {
                inst["name"]: _load_instrument(inst)
                for inst in sdict["instruments"]
            },
            "porter": sdict["porter"],
            "game": sdict["game"],
            "start_measure": sdict.get("start_measure", 1),
        },
    }

    return project


###############################################################################
# API function definitions
###############################################################################


def load(fname: Path) -> v2.ProjectDict:
    with open(fname, "r", encoding="utf8") as fobj:
        contents: SaveDict = yaml.safe_load(fobj)

    assert contents["save_version"] == 0

    return v1.to_v2(fname, to_v1(fname, contents))
