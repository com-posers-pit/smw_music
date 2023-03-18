#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard save functionality."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import datetime
from pathlib import Path
from typing import TypedDict

# Library imports
import yaml
from music21.pitch import Pitch

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
    NoteHead,
    SampleSource,
)
from smw_music.ui.state import State

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
    name: str
    mute: bool
    solo: bool
    samples: list["_SampleDict"]


###############################################################################


class _SampleDict(TypedDict):
    name: str
    octave: int
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
    notehead: int
    start: str


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
    return InstrumentConfig(
        name=inst["name"],
        samples=[_load_sample(x) for x in inst["samples"]],
        mute=inst["mute"],
        solo=inst["solo"],
    )


###############################################################################


def _load_sample(inst: _SampleDict) -> InstrumentSample:
    return InstrumentSample(
        name=inst["name"],
        octave=inst["octave"],
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
        ulim=Pitch(inst["ulim"]),
        llim=Pitch(inst["ulim"]),
        notehead=NoteHead(inst["notehead"]),
        start=Pitch(inst["start"]),
    )


###############################################################################


def _save_echo(echo: EchoConfig) -> _EchoDict:
    return {
        "enables": list(x.value for x in echo.enables),
        "vol_mag": list(echo.vol_mag),
        "vol_inv": list(echo.vol_inv),
        "delay": echo.delay,
        "fb_mag": echo.fb_mag,
        "fb_inv": echo.fb_inv,
        "fir_filt": echo.fir_filt,
    }


###############################################################################


def _save_instrument(inst: InstrumentConfig) -> _InstrumentDict:
    return {
        "name": inst.name,
        "mute": inst.mute,
        "solo": inst.solo,
        "samples": [_save_sample(x) for x in inst.samples],
    }


###############################################################################


def _save_sample(sample: InstrumentSample) -> _SampleDict:
    return {
        "name": sample.name,
        "octave": sample.octave,
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
        "adsr_mode": sample.adsr_mode,
        "attack_setting": sample.attack_setting,
        "decay_setting": sample.decay_setting,
        "sus_level_setting": sample.sus_level_setting,
        "sus_rate_setting": sample.sus_rate_setting,
        "gain_mode": sample.gain_mode.value,
        "gain_setting": sample.gain_setting,
        "tune_setting": sample.tune_setting,
        "subtune_setting": sample.subtune_setting,
        "mute": sample.mute,
        "solo": sample.solo,
        "ulim": str(sample.ulim),
        "llim": str(sample.llim),
        "notehead": sample.notehead.value,
        "start": str(sample.start),
    }


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
    state = State(
        musicxml_fname=Path(sdict["musicxml_fname"]),
        mml_fname=Path(sdict["mml_fname"]),
        loop_analysis=sdict["loop_analysis"],
        measure_numbers=sdict["measure_numbers"],
        global_volume=sdict["global_volume"],
        global_legato=sdict["global_legato"],
        global_echo_enable=sdict["global_echo_enable"],
        echo=_load_echo(sdict["echo"]),
        instruments=[_load_instrument(inst) for inst in sdict["instruments"]],
        project_name=project,
        porter=sdict["porter"],
        game=sdict["game"],
        start_measure=sdict.get("start_measure", 1),
    )

    return state


###############################################################################


def save(fname: Path, state: State) -> None:
    contents = {
        "tool_version": __version__,
        "save_version": _CURRENT_SAVE_VERSION,
        "song": state.project_name,
        "time": f"{datetime.datetime.utcnow()}",
        "state": {
            "musicxml_fname": str(state.musicxml_fname),
            "mml_fname": str(state.mml_fname),
            "loop_analysis": state.loop_analysis,
            "measure_numbers": state.measure_numbers,
            "global_volume": state.global_volume,
            "global_legato": state.global_legato,
            "global_echo_enable": state.global_echo_enable,
            "echo": _save_echo(state.echo),
            "instruments": [
                _save_instrument(inst) for inst in state.instruments
            ],
            "porter": state.porter,
            "game": state.game,
            "start_measure": state.start_measure,
        },
    }

    with open(fname, "w", encoding="utf8") as fobj:
        yaml.safe_dump(contents, fobj)
    state.unsaved = False
