# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""SPCMW Project settings."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import shutil
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Library imports
import yaml

# Package imports
from smw_music import __version__
from smw_music.ext_tools.amk import (
    N_BUILTIN_SAMPLES,
    BuiltinSampleGroup,
    BuiltinSampleSource,
    make_vis_dir,
)
from smw_music.song import Dynamics, NoteHead
from smw_music.spc700 import EchoConfig, Envelope, GainMode

from . import advanced
from .common import SpcmwException
from .instrument import (
    Artic,
    ArticSetting,
    InstrumentConfig,
    InstrumentSample,
    Pitch,
    SampleSource,
)
from .saves import v0, v1
from .stypes import AdvDict, EchoDict, InstrumentDict, ProjectDict, SampleDict

###############################################################################
# API constant definitions
###############################################################################

CURRENT_SAVE_VERSION = 2
EXTENSION = "spcmw"


###############################################################################
# Private function definitions
###############################################################################


def _load_adv(adv: AdvDict) -> advanced.Advanced:
    match adv["adv_type"]:
        case advanced.AdvType.NOP.value:
            return advanced.Nop()
        case advanced.AdvType.ECHO_FADE.value:
            return advanced.EchoFade(
                duration=adv["params"][0],
                final_volume=(adv["params"][1], adv["params"][2]),
            )
        case advanced.AdvType.GLISSANDO.value:
            return advanced.Glissando(
                duration=adv["params"][0], semitones=adv["params"][1]
            )
        case advanced.AdvType.GVOLUME_FADE.value:
            return advanced.GVolumeFade(
                duration=adv["params"][0], volume=adv["params"][1]
            )
        case advanced.AdvType.PAN_FADE.value:
            return advanced.PanFade(
                duration=adv["params"][0], pan=adv["params"][1]
            )
        case advanced.AdvType.PITCH_BEND.value:
            return advanced.PitchBend(
                delay=adv["params"][0],
                duration=adv["params"][1],
                offset=adv["params"][2],
            )
        case advanced.AdvType.PITCH_ENV_ATT.value:
            return advanced.PitchEnvAtt(
                delay=adv["params"][0],
                duration=adv["params"][1],
                semitones=adv["params"][2],
            )
        case advanced.AdvType.PITCH_ENV_REL.value:
            return advanced.PitchEnvRel(
                delay=adv["params"][0],
                duration=adv["params"][1],
                semitones=adv["params"][2],
            )
        case advanced.AdvType.TREMOLO.value:
            return advanced.Tremolo(
                delay=adv["params"][0],
                duration=adv["params"][1],
                amplitude=adv["params"][2],
            )
        case advanced.AdvType.VIBRATO.value:
            return advanced.Vibrato(
                delay=adv["params"][0],
                duration=adv["params"][1],
                amplitude=adv["params"][2],
            )
        case advanced.AdvType.VOLUME_FADE.value:
            return advanced.VolumeFade(
                duration=adv["params"][0],
                volume=adv["params"][1],
            )
        case _:
            return advanced.Advanced()


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


def _save_adv(adv: advanced.Advanced) -> AdvDict:
    types = advanced.AdvType
    match adv:
        case advanced.EchoFade(dur, final_volume):
            dval = (types.ECHO_FADE, [dur, final_volume[0], final_volume[1]])
        case advanced.Glissando(dur, semitones):
            dval = (types.GLISSANDO, [dur, semitones])
        case advanced.GVolumeFade(dur, volume):
            dval = (types.GLISSANDO, [dur, volume])
        case advanced.Nop:
            dval = (types.NOP, [])
        case advanced.PanFade(dur, pan):
            dval = (types.PAN_FADE, [dur, pan])
        case advanced.PitchBend(delay, dur, offset):
            dval = (types.PITCH_BEND, [delay, dur, offset])
        case advanced.PitchEnvAtt(delay, dur, semitones):
            dval = (types.PITCH_ENV_ATT, [delay, dur, semitones])
        case advanced.PitchEnvRel(delay, dur, semitones):
            dval = (types.PITCH_ENV_REL, [delay, dur, semitones])
        case advanced.Tremolo(delay, dur, ampl):
            dval = (types.TREMOLO, [delay, dur, ampl])
        case advanced.Vibrato(delay, dur, ampl):
            dval = (types.VIBRATO, [delay, dur, ampl])
        case advanced.VolumeFade(dur, vol):
            dval = (types.VIBRATO, [dur, vol])
        case _:
            dval = (types.NOP, [])

    return {"adv_type": dval[0].value, "params": dval[1]}


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


def _upgrade_save(fname: Path) -> Path:
    with open(fname, "r", encoding="utf8") as fobj:
        contents = yaml.safe_load(fobj)

    save_version = contents["save_version"]

    # Visualization support added in the middle of support for v1 version
    # files, so we should try to add it
    if save_version <= 1:
        make_vis_dir(fname.parent)
        _update_convert_scripts(fname.parent)

    backup = fname.parent / (fname.name + f".v{save_version}")
    shutil.copy(fname, backup)

    return backup


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
    global_echo: bool = True
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
    advanced: dict[str, advanced.Advanced] = field(default_factory=dict)

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
    path: Path | None = None
    info: ProjectInfo | None = None
    settings: ProjectSettings = field(default_factory=ProjectSettings)

    ###########################################################################

    @classmethod
    def load(cls, fname: Path) -> tuple["Project", Path | None]:
        with open(fname, "r", encoding="utf8") as fobj:
            contents: ProjectDict = yaml.safe_load(fobj)

        backup = None
        save_version = contents["save_version"]
        if save_version > CURRENT_SAVE_VERSION:
            raise SpcmwException(
                f"Save file version is {save_version}, tool version only "
                + f"supports up to {CURRENT_SAVE_VERSION}"
            )
        elif save_version < CURRENT_SAVE_VERSION:
            backup = _upgrade_save(fname)

            match save_version:
                case 0:
                    contents = v0.load(fname)
                case 1:
                    contents = v1.load(fname)

        project = cls(
            fname,
            ProjectInfo(
                Path(contents["musicxml"]),
                contents["project_name"],
                contents["composer"],
                contents["title"],
                contents["porter"],
                contents["game"],
            ),
            ProjectSettings(
                contents["amk_settings"]["loop_analysis"],
                contents["amk_settings"]["superloop_analysis"],
                contents["amk_settings"]["measure_numbers"],
                {
                    k: _load_instrument(v)
                    for k, v in contents["instruments"].items()
                },
                contents["amk_settings"]["global_volume"],
                contents["amk_settings"]["global_legato"],
                contents["global_echo"],
                _load_echo(contents["echo"]),
                BuiltinSampleGroup(
                    contents["amk_settings"]["builtin_sample_group"]
                ),
                list(
                    map(
                        BuiltinSampleSource,
                        contents["amk_settings"]["builtin_sample_sources"],
                    )
                ),
            ),
        )

        return project, backup

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
            "global_echo": settings.global_echo,
            "echo": _save_echo(settings.echo),
            "instruments": {
                k: _save_instrument(v) for k, v in settings.instruments.items()
            },
            "advanced": {
                k: _save_adv(v) for k, v in settings.advanced.items()
            },
            "amk_settings": {
                "loop_analysis": settings.loop_analysis,
                "superloop_analysis": settings.superloop_analysis,
                "measure_numbers": settings.measure_numbers,
                "global_volume": settings.global_volume,
                "global_legato": settings.global_legato,
                "builtin_sample_group": settings.builtin_sample_group.value,
                "builtin_sample_sources": [
                    x.value for x in settings.builtin_sample_sources
                ],
            },
        }

        with open(fname, "w", encoding="utf8") as fobj:
            yaml.safe_dump(contents, fobj)
