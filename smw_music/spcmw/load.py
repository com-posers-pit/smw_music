# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard save functionality."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import shutil
from pathlib import Path

# Library imports
import yaml
from music21.pitch import Pitch

# Package imports
from smw_music import SmwMusicException
from smw_music.amk import BuiltinSampleGroup, BuiltinSampleSource
from smw_music.music_xml.instrument import (
    Artic,
    ArticSetting,
    Dynamics,
    InstrumentConfig,
    InstrumentSample,
    NoteHead,
    SampleSource,
)
from smw_music.spc700 import Envelope, GainMode

from .echo import EchoConfig
from .old_save import v0, v1
from .project import (
    CURRENT_SAVE_VERSION,
    Project,
    ProjectInfo,
    ProjectSettings,
)
from .stypes import EchoDict, InstrumentDict, ProjectDict, SampleDict

###############################################################################
# Private function definitions
###############################################################################


def _load_echo(echo: EchoDict) -> EchoConfig:
    return EchoConfig(
        vol_mag=(echo["vol_mag"][0], echo["vol_mag"][1]),
        vol_inv=(echo["vol_inv"][0], echo["vol_inv"][1]),
        delay=echo["delay"],
        fb_mag=echo["fb_mag"],
        fb_inv=echo["fb_inv"],
        fir_filt=echo["fir_filt"],
    )


###############################################################################


def _load_instrument(inst: InstrumentDict) -> InstrumentConfig:
    rv = InstrumentConfig(
        mute=inst["mute"],
        solo=inst["solo"],
    )
    # This is a property setter, not a field in the dataclass, so it has to be
    # set ex post facto
    rv.samples = {k: _load_sample(v) for k, v in inst["samples"].items()}

    return rv


###############################################################################


def _load_sample(inst: SampleDict) -> InstrumentSample:
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


def _upgrade_save(fname: Path) -> tuple[Project, Path]:
    with open(fname, "r", encoding="utf8") as fobj:
        contents = yaml.safe_load(fobj)

    save_version = contents["save_version"]

    backup = fname.parent / (fname.name + f".v{save_version}")
    shutil.copy(fname, backup)

    match save_version:
        case 0:
            project = v0.load(fname)
        case 1:
            project = v1.load(fname)

    return project, backup


###############################################################################
# API function definitions
###############################################################################


def load(fname: Path) -> tuple[Project, Path | None]:
    rv: tuple[Project, Path | None]

    with open(fname, "r", encoding="utf8") as fobj:
        contents: ProjectDict = yaml.safe_load(fobj)

    save_version = contents["save_version"]
    if save_version > CURRENT_SAVE_VERSION:
        raise SmwMusicException(
            f"Save file version is {save_version}, tool version only "
            + f"supports up to {CURRENT_SAVE_VERSION}"
        )

    if save_version < CURRENT_SAVE_VERSION:
        rv = _upgrade_save(fname)
    else:
        musicxml = Path(contents["musicxml_fname"])

        proj_dir = fname.parent.resolve()

        # Convert to absolute path if needed
        if not musicxml.is_absolute():
            musicxml = proj_dir / musicxml

        project = Project(
            ProjectInfo(
                musicxml,
                contents["project_name"],
                contents["composer"],
                contents["title"],
                contents["porter"],
                contents["game"],
            ),
            ProjectSettings(
                contents["loop_analysis"],
                contents["superloop_analysis"],
                contents["measure_numbers"],
                {
                    k: _load_instrument(v)
                    for k, v in contents["instruments"].items()
                },
                contents["global_volume"],
                contents["global_legato"],
                _load_echo(contents["echo"]),
                BuiltinSampleGroup(contents["builtin_sample_group"]),
                list(
                    map(
                        BuiltinSampleSource, contents["builtin_sample_sources"]
                    )
                ),
            ),
        )
        rv = project, None

    return rv
