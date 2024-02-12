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
import shutil
from contextlib import suppress
from dataclasses import fields
from pathlib import Path
from typing import Callable, TypedDict, cast

# Library imports
import yaml
from music21.pitch import Pitch

# Package imports
from smw_music import SmwMusicException
from smw_music.amk import make_vis_dir
from smw_music.song.echo import EchoCh, EchoConfig
from smw_music.song.instrument import (
    Artic,
    ArticSetting,
    Dynamics,
    InstrumentConfig,
    InstrumentSample,
    NoteHead,
    SampleSource,
)
from smw_music.spc700 import Envelope, GainMode
from smw_music.ui.old_save import v0
from smw_music.ui.state import BuiltinSampleGroup, BuiltinSampleSource, State

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
    rv.samples = {k: _load_sample(v) for k, v in inst["samples"].items()}

    return rv


###############################################################################


def _load_sample(inst: _SampleDict) -> InstrumentSample:
    return InstrumentSample(
        octave_shift=inst["octave_shift"],
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
        envelope=Envelope(
            adsr_mode=inst["adsr_mode"],
            attack_setting=inst["attack_setting"],
            decay_setting=inst["decay_setting"],
            sus_level_setting=inst["sus_level_setting"],
            sus_rate_setting=inst["sus_rate_setting"],
            gain_mode=GainMode(inst["gain_mode"]),
            gain_setting=inst["gain_setting"],
        ),
        tune_setting=inst["tune_setting"],
        subtune_setting=inst["subtune_setting"],
        mute=inst["mute"],
        solo=inst["solo"],
        ulim=Pitch(inst["ulim"]),
        llim=Pitch(inst["llim"]),
        notehead=NoteHead(inst["notehead"]),
        start=Pitch(inst["start"]),
        track=bool(inst.get("track", False)),
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
        "mute": inst.mute,
        "solo": inst.solo,
        "samples": {k: _save_sample(v) for k, v in inst.samples.items()},
    }


###############################################################################


def _save_sample(sample: InstrumentSample) -> _SampleDict:
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


def _upgrade_save(fname: Path) -> tuple[State, Path]:
    with open(fname, "r", encoding="utf8") as fobj:
        contents = yaml.safe_load(fobj)

    save_version = contents["save_version"]

    backup = fname.parent / (fname.name + f".v{save_version}")
    shutil.copy(fname, backup)

    assert save_version == 0  # nosec: B101
    state = v0.load(fname)

    return state, backup


###############################################################################


def _update_convert_scripts(dirname: Path) -> None:
    for fname in ["convert.bat", "convert.sh"]:
        fpath = dirname / fname

        with open(fpath, "r", encoding="utf8") as fobj:
            lines = fobj.readlines()

        for n, line in enumerate(lines):
            if "AddmusicK" in line and "-visualize" not in line:
                split = line.split('"')
                split[0] += "-visualize "
                line = '"'.join(split)
                lines[n] = line

        with open(fpath, "w", encoding="utf8") as fobj:
            fobj.write("".join(lines))


###############################################################################
# API function definitions
###############################################################################


def load(fname: Path) -> tuple[State, Path | None]:
    rv: tuple[State, Path | None]

    with open(fname, "r", encoding="utf8") as fobj:
        contents: _SaveDict = yaml.safe_load(fobj)

    save_version = contents["save_version"]
    if save_version > _CURRENT_SAVE_VERSION:
        raise SmwMusicException(
            f"Save file version is {save_version}, tool version only "
            + f"supports up to {_CURRENT_SAVE_VERSION}"
        )

    # Visualization support added in the middle of support for v1 version
    # files, so we should try to add it
    if save_version <= 1:
        make_vis_dir(fname.parent)
        _update_convert_scripts(fname.parent)

    if save_version < _CURRENT_SAVE_VERSION:
        rv = _upgrade_save(fname)
    else:
        project = contents["song"]
        sdict = contents["state"]
        musicxml: Path | str | None = sdict["musicxml_fname"]
        mml: Path | str | None = sdict["mml_fname"]

        proj_dir = fname.parent.resolve()

        # Convert to absolute path if needed
        if musicxml is not None:
            musicxml = Path(musicxml)
            if not musicxml.is_absolute():
                musicxml = proj_dir / musicxml
        if mml is not None:
            mml = Path(mml)
            if not mml.is_absolute():
                mml = proj_dir / mml

        state_fields = {x.name: x for x in fields(State)}

        state = State(
            musicxml_fname=None if musicxml is None else musicxml,
            mml_fname=None if mml is None else mml,
            loop_analysis=sdict["loop_analysis"],
            measure_numbers=sdict["measure_numbers"],
            global_volume=sdict["global_volume"],
            global_legato=sdict["global_legato"],
            global_echo_enable=sdict["global_echo_enable"],
            echo=_load_echo(sdict["echo"]),
            instruments={
                k: _load_instrument(v) for k, v in sdict["instruments"].items()
            },
            project_name=project,
            porter=sdict["porter"],
            game=sdict["game"],
            start_measure=sdict.get(
                "start_measure",
                cast(int, state_fields["start_measure"].default),
            ),
            builtin_sample_group=BuiltinSampleGroup(
                sdict.get(
                    "builtin_sample_group",
                    state_fields["builtin_sample_group"].default,
                )
            ),
            builtin_sample_sources=[
                BuiltinSampleSource(x)
                for x in sdict.get(
                    "builtin_sample_sources",
                    cast(
                        Callable[[], list[BuiltinSampleSource]],
                        state_fields["builtin_sample_sources"].default_factory,
                    )(),
                )
            ],
        )
        rv = state, None

    return rv
