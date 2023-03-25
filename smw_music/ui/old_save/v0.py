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
from smw_music import SmwMusicException, __version__
from smw_music.music_xml.echo import EchoCh, EchoConfig
from smw_music.music_xml.instrument import (
    Artic,
    ArticSetting,
    Dynamics,
    GainMode,
    InstrumentConfig,
    InstrumentSample,
    SampleSource,
)
from smw_music.ui.state import State

###############################################################################
# Private constant definitions
###############################################################################

_CURRENT_SAVE_VERSION = 0

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


class _SaveDict(TypedDict):
    tool_version: str
    save_version: int
    song: str
    time: str
    state: "_StateDict"


###############################################################################


class _StateDict(TypedDict):
    musicxml_fname: str
    mml_fname: str
    loop_analysis: bool
    measure_numbers: bool
    instrument_idx: int
    global_volume: bool
    global_legato: bool
    global_echo_enable: bool
    echo: _EchoDict
    instruments: list[_InstrumentDict]
    porter: str
    game: str
    start_measure: int


###############################################################################
# Private function definitions
###############################################################################


def _load_echo(echo: _EchoDict) -> EchoConfig:
    return EchoConfig(
        enables=set(EchoCh(x) for x in echo["enables"]),
        vol_mag=(echo["vol_mag"][0], echo["vol_mag"][1]),
        vol_inv=(echo["vol_inv"][0], echo["vol_inv"][1]),
        delay=echo["delay"],
        fb_mag=echo["fb_mag"],
        fb_inv=echo["fb_inv"],
        fir_filt=echo["fir_filt"],
    )


###############################################################################


def _load_instrument(inst: _InstrumentDict) -> InstrumentConfig:
    rv = InstrumentConfig(
        mute=inst["mute"],
        solo=inst["solo"],
    )

    # This is a property setter, not a field in the dataclass, so it has to be
    # set ex post facto
    rv.samples = {"": _load_sample(inst)}

    return rv


###############################################################################


def _load_sample(inst: _InstrumentDict) -> InstrumentSample:
    rv = InstrumentSample(
        dynamics={Dynamics(k): v for k, v in inst["dynamics"].items()},
        dyn_interpolate=inst["interpolate_dynamics"],
        artics={
            Artic(k): ArticSetting(v[0], v[1])
            for k, v in inst["articulations"].items()
        },
        pan_enabled=inst["pan_enabled"],
        pan_setting=inst["pan_setting"],
        pan_invert=(
            inst.get("pan_l_invert", False),
            inst.get("pan_r_invert", False),
        ),
        sample_source=SampleSource(inst["sample_source"]),
        builtin_sample_index=inst["builtin_sample_index"],
        pack_sample=(inst["pack_sample"][0], Path(inst["pack_sample"][1])),
        brr_fname=Path(inst["brr_fname"]),
        adsr_mode=inst["adsr_mode"],
        attack_setting=inst["attack_setting"],
        decay_setting=inst["decay_setting"],
        sus_level_setting=inst["sus_level_setting"],
        sus_rate_setting=inst["sus_rate_setting"],
        gain_mode=GainMode(inst["gain_mode"]),
        gain_setting=inst["gain_setting"],
        tune_setting=inst["tune_setting"],
        subtune_setting=inst["subtune_setting"],
        mute=inst["mute"],
        solo=inst["solo"],
    )

    rv.octave_shift = inst["octave"] - rv.default_octave

    return rv


###############################################################################
# API function definitions
###############################################################################


def load(fname: Path) -> State:
    with open(fname, "r", encoding="utf8") as fobj:
        contents: _SaveDict = yaml.safe_load(fobj)

    save_version = contents["save_version"]
    if contents["save_version"] > _CURRENT_SAVE_VERSION:
        raise SmwMusicException(
            f"Save file version is {save_version}, tool version only "
            + f"supports up to {_CURRENT_SAVE_VERSION}"
        )

    project = contents["song"]
    sdict = contents["state"]
    if param_fname := sdict["musicxml_fname"]:
        musicxml_fname = Path(param_fname).resolve()
    else:
        musicxml_fname = None
    if param_fname := sdict["mml_fname"]:
        mml_fname = Path(param_fname).resolve()
    else:
        mml_fname = None

    state = State(
        musicxml_fname=musicxml_fname,
        mml_fname=mml_fname,
        loop_analysis=sdict["loop_analysis"],
        measure_numbers=sdict["measure_numbers"],
        global_volume=sdict["global_volume"],
        global_legato=sdict["global_legato"],
        global_echo_enable=sdict["global_echo_enable"],
        echo=_load_echo(sdict["echo"]),
        instruments={
            inst["name"]: _load_instrument(inst)
            for inst in sdict["instruments"]
        },
        project_name=project,
        porter=sdict["porter"],
        game=sdict["game"],
        start_measure=sdict.get("start_measure", 1),
    )

    return state
