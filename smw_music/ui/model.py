#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Music XML -> AMK Converter."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import configparser
import json
import os
import pkgutil
import platform
import shutil
import stat
import subprocess
import threading
import zipfile
from enum import IntEnum, auto
from pathlib import Path

# Library imports
from mako.template import Template  # type: ignore
from PyQt6.QtCore import QObject, pyqtSignal

# Package imports
from smw_music import SmwMusicException, __version__
from smw_music.log import debug, info
from smw_music.music_xml import InstrumentConfig, MusicXmlException
from smw_music.music_xml.echo import EchoConfig
from smw_music.music_xml.song import Song

###############################################################################
# Private Function Definitions
###############################################################################


def _dyn_to_str(dyn: "_DynEnum") -> str:
    lut = {
        _DynEnum.PPPP: "PPPP",
        _DynEnum.PPP: "PPP",
        _DynEnum.PP: "PP",
        _DynEnum.P: "P",
        _DynEnum.MP: "MP",
        _DynEnum.MF: "MF",
        _DynEnum.F: "F",
        _DynEnum.FF: "FF",
        _DynEnum.FFF: "FFF",
        _DynEnum.FFFF: "FFFF",
    }
    return lut[dyn]


###############################################################################


def _str_to_dyn(dyn: str) -> "_DynEnum":
    lut = {
        "PPPP": _DynEnum.PPPP,
        "PPP": _DynEnum.PPP,
        "PP": _DynEnum.PP,
        "P": _DynEnum.P,
        "MP": _DynEnum.MP,
        "MF": _DynEnum.MF,
        "F": _DynEnum.F,
        "FF": _DynEnum.FF,
        "FFF": _DynEnum.FFF,
        "FFFF": _DynEnum.FFFF,
    }
    return lut[dyn]


###############################################################################
# Private Class Definitions
###############################################################################


class _DynEnum(IntEnum):
    PPPP = auto()
    PPP = auto()
    PP = auto()
    P = auto()
    MP = auto()
    MF = auto()
    F = auto()
    FF = auto()
    FFF = auto()
    FFFF = auto()


###############################################################################
# API Class Definitions
###############################################################################


class Model(QObject):
    inst_config_changed = pyqtSignal(InstrumentConfig)  # arguments=["config"]
    mml_generated = pyqtSignal(str)  # arguments=['mml']
    response_generated = pyqtSignal(
        bool, str, str
    )  # arguments=["error", "title", "response"]
    song_changed = pyqtSignal(Song)  # arguments=["song"]

    song: Song | None
    mml_fname: str
    global_legato: bool
    loop_analysis: bool
    superloop_analysis: bool
    measure_numbers: bool
    custom_samples: bool
    custom_percussion: bool
    active_instrument: InstrumentConfig
    _disable_interp: bool
    _amk_path: Path | None = None
    _spcplay_path: Path | None = None
    _project_file: Path | None = None
    _project_name: str | None = None

    ###########################################################################

    @debug()
    def __init__(self) -> None:
        super().__init__()
        self.song = None
        self.mml_fname = ""
        self.global_legato = False
        self.loop_analysis = False
        self.superloop_analysis = False
        self.measure_numbers = False
        self.custom_samples = False
        self.custom_percussion = False
        self.instruments = None
        self.active_instrument = InstrumentConfig("")
        self._disable_interp = False

        self._load_prefs()

    ###########################################################################
    # API method definitions
    ###########################################################################

    @info(True)
    def convert_mml(self) -> None:
        print(self._project_path)
        subprocess.call(["sh", "convert.sh"], cwd=self._project_path)

    ###########################################################################

    @info(True)
    def create_project(
        self, project_file: Path, project_name: str | None = None
    ) -> None:
        self._project_file = project_file
        self._project_name = project_name or project_file.stem

        members = [
            "1DF9",
            "AddmusicK.exe",
            "Addmusic_sample groups.txt",
            "asar.exe",
            "music",
            "SPCs",
            "1DFC",
            "Addmusic_list.txt",
            "Addmusic_sound effects.txt",
            "asm",
            "samples",
        ]

        path = self._project_path
        assert path is not None

        with zipfile.ZipFile(str(self._amk_path), "r") as zobj:
            # Extract all the files
            zobj.extractall(path=path)

            names = zobj.namelist()
            root = sorted(names, key=len)[0]

            # Move them up a directory and delete the rest
            for member in members:
                shutil.move(path / root / member, path / member)

            shutil.rmtree(path / root)

        # Create the conversion scripts
        for tmpl_name in ["convert.bat", "convert.sh"]:
            tmpl = (
                Template(  # nosec - generates a .txt output, no XSS concerns
                    pkgutil.get_data("smw_music", f"data/{tmpl_name}")
                )
            )
            script = tmpl.render(project=self._project_name)
            target = path / tmpl_name

            with open(target, "w", encoding="utf8") as fobj:
                fobj.write(script)

            os.chmod(target, os.stat(target).st_mode | stat.S_IXUSR)

        self.save()

    ###########################################################################

    @info(True)
    def generate_mml(self, fname: str, echo: EchoConfig | None) -> None:
        title = "MML Generation"
        error = True
        if self.song is None:
            msg = "Song not loaded"
        else:
            try:
                if os.path.exists(fname):
                    shutil.copy2(fname, f"{fname}.bak")
                mml = self.song.to_mml_file(
                    fname,
                    self.global_legato,
                    self.loop_analysis,
                    self.superloop_analysis,
                    self.measure_numbers,
                    True,
                    echo,
                    self.custom_samples,
                    self.custom_percussion,
                )
                self.mml_generated.emit(mml)
            except MusicXmlException as e:
                msg = str(e)
            else:
                error = False
                msg = "Done"
        self.response_generated.emit(error, title, msg)

    ###########################################################################

    @info(True)
    def load(self, fname: str) -> None:
        with open(fname, "r", encoding="utf8") as fobj:
            contents = json.load(fobj)

        self._project_name = contents["song"]
        self._project_file = Path(fname)
        self.mml_fname = contents["mml"]
        self.global_legato = contents["global_legato"]
        self.loop_analysis = contents["loop_analysis"]
        self.superloop_analysis = contents["superloop_analysis"]
        self.measure_numbers = contents["measure_numbers"]
        self.custom_samples = contents["custom_samples"]
        self.custom_percussion = contents["custom_percussion"]
        self._disable_interp = contents["disable_interp"]

    ###########################################################################

    @info(True)
    def play_spc(self) -> None:
        path = self._project_path

        if path is not None:
            spc_name = self._project_name
            assert spc_name is not None

            spc_name = f"{spc_name}.spc"
            spc_name = str(path / "SPCs" / spc_name)
            threading.Thread(
                target=subprocess.call,
                args=(["wine", str(self._spcplay_path), spc_name],),
            ).start()

    ###########################################################################

    @info(True)
    def save(self) -> None:
        contents = {
            "version": __version__,
            "song": self._project_name,
            "mml": self.mml_fname,
            "global_legato": self.global_legato,
            "loop_analysis": self.loop_analysis,
            "superloop_analysis": self.superloop_analysis,
            "measure_numbers": self.measure_numbers,
            "custom_samples": self.custom_samples,
            "custom_percussion": self.custom_percussion,
            "disable_interp": self._disable_interp,
            "instruments": "",
            "samples": "",
        }

        if self._project_file is not None:
            with open(self._project_file, "w", encoding="utf8") as fobj:
                json.dump(contents, fobj)

    ###########################################################################

    @info(True)
    def save_as(self, fname: str) -> None:
        self._project_file = Path(fname)
        self.save()

    ###########################################################################

    @info(True)
    def set_instrument(self, name: str) -> None:
        if self.song is not None:
            for inst in self.song.instruments:
                if inst.name == name:
                    self.active_instrument = inst
                    self._disable_interp = True
                    self.inst_config_changed.emit(inst)
                    self._disable_interp = False
                    break

    ###########################################################################

    @info()
    def set_config(
        self,
        global_legato: bool,
        loop_analysis: bool,
        superloop_analysis: bool,
        measure_numbers: bool,
        custom_samples: bool,
        custom_percussion: bool,
    ) -> None:
        self.global_legato = global_legato
        self.loop_analysis = loop_analysis
        self.superloop_analysis = superloop_analysis
        self.measure_numbers = measure_numbers
        self.custom_samples = custom_samples
        self.custom_percussion = custom_percussion

    ###########################################################################

    @info(True)
    def set_pan(self, enabled: bool, pan: int) -> None:
        if self.song is not None:
            self.active_instrument.pan = pan if enabled else None

    ###########################################################################

    @info(True)
    def set_song(self, fname: str) -> None:
        try:
            self.song = Song.from_music_xml(fname)
        except MusicXmlException as e:
            self.response_generated.emit(True, "Song load", str(e))
        else:
            self._signal()

    ###########################################################################

    @info(True)
    def update_artic(self, artic: str, quant: int) -> None:
        if self.song is not None:
            self.active_instrument.quant[artic] = quant

    ###########################################################################

    @info(True)
    def update_dynamics(self, dyn: str, val: int, interp: bool) -> None:
        if self.song is not None:
            if dyn == "global":
                self.song.volume = val
            else:
                self.active_instrument.dynamics[dyn] = val
                if interp and not self._disable_interp:
                    self._interpolate(dyn, val)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _load_prefs(self) -> None:
        if not self.prefs.exists():
            self._init_prefs()

        parser = configparser.ConfigParser()
        parser.read(self.prefs)

        self._amk_path = Path(parser["paths"]["amk"])
        self._spcplay_path = Path(parser["paths"]["spcplay"])

    ###########################################################################

    @debug()
    def _interpolate(self, dyn_str: str, level: int) -> None:
        self._disable_interp = True

        moved_dyn = _str_to_dyn(dyn_str)
        dyns = [
            _str_to_dyn(x) for x in self.active_instrument.dynamics_present
        ]

        min_dyn = min(dyns)
        max_dyn = max(dyns)

        min_val = self.active_instrument.dynamics[_dyn_to_str(min_dyn).upper()]
        max_val = self.active_instrument.dynamics[_dyn_to_str(max_dyn).upper()]

        if moved_dyn != min_dyn:
            level = max(min_val, level)
        if moved_dyn != max_dyn:
            level = min(max_val, level)

        for dyn in dyns:
            if dyn == moved_dyn:
                val = level
            elif dyn in [min_dyn, max_dyn]:
                continue
            if dyn < moved_dyn:
                numer = 1 + sum(dyn < x < moved_dyn for x in dyns)
                denom = 1 + sum(min_dyn < x < moved_dyn for x in dyns)
                val = round(
                    min_val + (level - min_val) * (denom - numer) / denom
                )
            elif dyn > moved_dyn:
                numer = 1 + sum(moved_dyn < x < dyn for x in dyns)
                denom = 1 + sum(moved_dyn < x < max_dyn for x in dyns)
                val = round(level + (max_val - level) * numer / denom)

            self.active_instrument.dynamics[_dyn_to_str(dyn)] = val

        self.inst_config_changed.emit(self.active_instrument)

        self._disable_interp = False

    ###########################################################################

    @debug()
    def _signal(self) -> None:
        self.song_changed.emit(self.song)

    ###########################################################################
    # Private property definitions
    ###########################################################################

    @property
    def _project_path(self) -> Path | None:
        file = self._project_file
        return None if file is None else file.parents[0]

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def prefs(self) -> Path:
        app = "xml2mml"
        prefs = "preferences.ini"

        match sys := platform.system():
            case "Linux":
                default = Path(os.environ["HOME"]) / ".config"
                conf_dir = Path(os.environ.get("XDG_CONFIG_HOME", default))
            case "Windows":
                conf_dir = Path(os.environ["APP_DATA"])
            case "Darwin":
                conf_dir = Path(os.environ["HOME"]) / "Library"
            case _:
                raise SmwMusicException(f"Unknown OS {sys}")

        return conf_dir / app / prefs
