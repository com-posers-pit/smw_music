# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Music XML -> AMK Converter."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import os
import pkgutil
import platform
import shutil
import stat
import subprocess  # nosec 404
import tempfile
import threading
import zipfile
from dataclasses import replace
from enum import IntEnum, auto
from pathlib import Path

# Library imports
import yaml
from mako.template import Template  # type: ignore
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QStandardItem, QStandardItemModel

# Package imports
from smw_music import SmwMusicException, __version__
from smw_music.log import debug, info
from smw_music.music_xml import InstrumentConfig, MusicXmlException
from smw_music.music_xml.echo import EchoConfig
from smw_music.music_xml.song import Song
from smw_music.ramfs import RamFs
from smw_music.ui.sample import Sample
from smw_music.ui.state import GainMode, SampleSource, State

###############################################################################
# Private Function Definitions
###############################################################################


def _add_brr_to_model(
    pack_item: QStandardItem,
    name: str,
    parents: dict[tuple[str, ...], QStandardItem],
    samples: dict[str, Sample] = {},
) -> None:
    fname = tuple(name.split("/"))

    parent = pack_item
    for n, path_item in enumerate(fname):
        partial_path = fname[: (n + 1)]
        try:
            parent = parents[partial_path]
        except KeyError:
            item = QStandardItem(path_item)
            parents[partial_path] = item
            parent.appendRow(item)
            parent = item


###############################################################################


def _add_sample_pack_to_model(
    model: QStandardItemModel, pack: str, path: Path
) -> None:

    parents: dict[tuple[str, ...], QStandardItem] = {}
    samples: dict[str, Sample] = {}

    with zipfile.ZipFile(path) as zobj:
        names = zobj.namelist()

    # Add the pack as a top-level item
    pack_item = QStandardItem(pack)
    model.appendRow(pack_item)

    for name in names:
        if name.endswith("!patterns.txt"):
            pass
        elif name.endswith(".brr"):
            _add_brr_to_model(pack_item, name, parents)


###############################################################################


def _parse_setting(val: int | str) -> int:
    if isinstance(val, int):
        return val

    val = val.strip()
    if val[-1] == "%":
        return int(255 * float(val[:-1]) / 100)
    if val[0] == "$":
        return int(val[1:], 16)
    return int(float(val))


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
    state_changed = pyqtSignal(State)
    instruments_changed = pyqtSignal(list)

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
    sample_packs_model: QStandardItemModel
    _history: list[State]
    _disable_interp: bool
    _amk_path: Path | None = None
    _sample_packs: dict[str, dict[str, str]] | None = None
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
        self.active_instrument = InstrumentConfig("")
        self.sample_packs_model = QStandardItemModel()
        self._disable_interp = False
        self._history = [State()]

        self._load_prefs()

    ###########################################################################
    # API method definitions
    ###########################################################################

    def reinforce_state(self) -> None:
        self.state_changed.emit(self.state)

    def _update_state(self, **kwargs) -> None:
        new_state = replace(self.state, **kwargs)
        if new_state != self.state:
            self._history.append(new_state)
            self.state_changed.emit(new_state)

    def on_musicxml_fname_changed(self, fname: str) -> None:
        try:
            self.song = Song.from_music_xml(fname)
        except MusicXmlException as e:
            self.response_generated.emit(True, "Song load", str(e))
        else:
            self.song_changed.emit(self.song)
            self.instruments_changed.emit(
                [x.name for x in self.song.instruments]
            )
        self._update_state(musicxml_fname=fname)

    def on_mml_fname_changed(self, fname: str) -> None:
        self._update_state(mml_fname=fname)

    def on_loop_analysis_changed(self, enabled: bool) -> None:
        self._update_state(loop_analysis=enabled)

    def on_superloop_analysis_changed(self, enabled: bool) -> None:
        self._update_state(superloop_analysis=enabled)

    def on_measure_numbers_changed(self, enabled: bool) -> None:
        self._update_state(measure_numbers=enabled)

    def on_generate_mml_clicked(self) -> None:
        pass

    def on_generate_spc_clicked(self) -> None:
        pass

    def on_play_spc_clicked(self) -> None:
        pass

    def on_pppp_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(pppp_setting=setting)

    def on_ppp_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(ppp_setting=setting)

    def on_pp_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(pp_setting=setting)

    def on_p_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(p_setting=setting)

    def on_mp_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(mp_setting=setting)

    def on_mf_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(mf_setting=setting)

    def on_f_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(f_setting=setting)

    def on_ff_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(ff_setting=setting)

    def on_fff_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(fff_setting=setting)

    def on_ffff_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(ffff_setting=setting)

    def on_interpolate_changed(self, state: bool) -> None:
        self._update_state(dyn_interpolate=state)

    def on_def_artic_length_changed(self, val: int) -> None:
        self._update_state(default_artic_length=val)

    def on_def_artic_volume_changed(self, val: int) -> None:
        self._update_state(default_artic_volume=val)

    def on_accent_length_changed(self, val: int) -> None:
        self._update_state(accent_length=val)

    def on_accent_volume_changed(self, val: int) -> None:
        self._update_state(accent_volume=val)

    def on_staccato_length_changed(self, val: int) -> None:
        self._update_state(staccato_length=val)

    def on_staccato_volume_changed(self, val: int) -> None:
        self._update_state(staccato_volume=val)

    def on_accstacc_length_changed(self, val: int) -> None:
        self._update_state(accstacc_length=val)

    def on_accstacc_volume_changed(self, val: int) -> None:
        self._update_state(accstacc_volume=val)

    def on_pan_enable_changed(self, state: bool) -> None:
        self._update_state(pan_enabled=state)

    def on_pan_setting_changed(self, val: int) -> None:
        self._update_state(pan_setting=val)

    def on_builtin_sample_selected(self, state: bool) -> None:
        if state:
            self._update_state(sample_source=SampleSource.BUILTIN)

    def on_builtin_sample_changed(self, index: int) -> None:
        self._update_state(builtin_sample_index=index)

    def on_pack_sample_selected(self, state: bool) -> None:
        if state:
            self._update_state(sample_source=SampleSource.SAMPLEPACK)

    def on_pack_sample_changed(self, index: int) -> None:
        new_state: dict[str, int | str] = {"pack_sample_index": index}
        if self.state.sample_source == SampleSource.SAMPLEPACK:
            new_state["brr_setting"] = "$80 $00 $00 $00 $00"

        self._update_state(**new_state)

    def on_brr_sample_selected(self, state: bool) -> None:
        if state:
            self._update_state(sample_source=SampleSource.BRR)

    def on_brr_fname_changed(self, fname: str) -> None:
        self._update_state(brr_fname=fname)

    def on_select_adsr_mode_selected(self, state: bool) -> None:
        self._update_state(adsr_mode=state)

    def on_gain_direct_selected(self, state: bool) -> None:
        if state:
            self._update_state(gain_mode=GainMode.DIRECT)

    def on_gain_inclin_selected(self, state: bool) -> None:
        if state:
            self._update_state(gain_mode=GainMode.INCLIN)

    def on_gain_incbent_selected(self, state: bool) -> None:
        if state:
            self._update_state(gain_mode=GainMode.INCBENT)

    def on_gain_declin_selected(self, state: bool) -> None:
        if state:
            self._update_state(gain_mode=GainMode.DECLIN)

    def on_gain_decexp_selected(self, state: bool) -> None:
        if state:
            self._update_state(gain_mode=GainMode.DECEXP)

    def on_gain_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(gain_setting=setting)

    def on_attack_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(attack_setting=setting)

    def on_decay_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(decay_setting=setting)

    def on_sus_level_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(sus_level_setting=setting)

    def on_sus_rate_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(sus_rate_setting=setting)

    def on_tune_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(tune_setting=setting)

    def on_subtune_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(subtune_setting=setting)

    def on_brr_setting_changed(self, val: str) -> None:
        self._update_state(brr_setting=val)

    def on_global_volume_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(global_volume=setting)

    def on_global_legato_changed(self, state: bool) -> None:
        self._update_state(global_legato=state)

    def on_echo_enable_changed(self, state: bool) -> None:
        self._update_state(echo_enable=state)

    def on_echo_ch0_changed(self, state: bool) -> None:
        self._update_state(echo_ch0_enable=state)

    def on_echo_ch1_changed(self, state: bool) -> None:
        self._update_state(echo_ch1_enable=state)

    def on_echo_ch2_changed(self, state: bool) -> None:
        self._update_state(echo_ch2_enable=state)

    def on_echo_ch3_changed(self, state: bool) -> None:
        self._update_state(echo_ch3_enable=state)

    def on_echo_ch4_changed(self, state: bool) -> None:
        self._update_state(echo_ch4_enable=state)

    def on_echo_ch5_changed(self, state: bool) -> None:
        self._update_state(echo_ch5_enable=state)

    def on_echo_ch6_changed(self, state: bool) -> None:
        self._update_state(echo_ch6_enable=state)

    def on_echo_ch7_changed(self, state: bool) -> None:
        self._update_state(echo_ch7_enable=state)

    def on_filter_0_toggled(self, state: bool) -> None:
        self._update_state(echo_filter0=state)

    def on_echo_left_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(echo_left_setting=setting)

    def on_echo_left_surround_changed(self, state: bool) -> None:
        # TODO
        pass

    def on_echo_right_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(echo_right_setting=setting)

    def on_echo_right_surround_changed(self, state: bool) -> None:
        # TODO
        pass

    def on_echo_feedback_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(echo_feedback_setting=setting)

    def on_echo_feedback_surround_changed(self, state: bool) -> None:
        # TODO
        pass

    def on_echo_delay_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(echo_delay_setting=setting)

    ###########################################################################

    def undo(self) -> None:
        if len(self._history) > 1:
            self._history.pop()
            self.state_changed.emit(self.state)

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
        # Since _project_file was set above this won't be None
        assert path is not None  # nosec 703

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
            tmpl = Template(  # nosec B702
                pkgutil.get_data("smw_music", f"data/{tmpl_name}")
            )
            script = tmpl.render(project=self._project_name)
            target = path / tmpl_name

            with open(target, "w", encoding="utf8") as fobj:
                fobj.write(script)

            os.chmod(target, os.stat(target).st_mode | stat.S_IXUSR)

        self.save()

    ###########################################################################

    @info(True)
    def load(self, fname: str) -> None:
        with open(fname, "r", encoding="utf8") as fobj:
            contents = yaml.safe_load(fobj)

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
    def on_mml_generated(self, fname: str, echo: EchoConfig | None) -> None:
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
    def on_spc_generated(self) -> None:
        # TODO: support OSX and windows
        subprocess.call(  # nosec B603, B607
            ["sh", "convert.sh"], cwd=self._project_path
        )

    ###########################################################################

    @info(True)
    def on_spc_played(self) -> None:
        path = self._project_path

        if path is not None:
            spc_name = self._project_name

            spc_name = f"{spc_name}.spc"
            spc_name = str(path / "SPCs" / spc_name)
            threading.Thread(
                target=subprocess.call,
                # TODO: Handle windows/OSX
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
            "samples": "",
        }

        if self._project_file is not None:
            with open(self._project_file, "w", encoding="utf8") as fobj:
                yaml.dump(contents, fobj)

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

    def _init_prefs(self) -> None:
        pass

    ###########################################################################

    def _load_sample_packs(self) -> None:
        assert self._sample_packs is not None  # nosec 703

        for pack_name, pack in self._sample_packs.items():
            _add_sample_pack_to_model(
                self.sample_packs_model, pack_name, Path(pack["path"])
            )

    ###########################################################################

    def _load_prefs(self) -> None:
        if not self.prefs.exists():
            self._init_prefs()

        with open(self.prefs, "r", encoding="utf8") as fobj:
            prefs = yaml.safe_load(fobj)

        self._amk_path = Path(prefs["amk"]["path"])
        self._sample_packs = prefs["sample_packs"]
        self._spcplay_path = Path(prefs["spcplay"]["path"])

        if self._sample_packs:
            self._load_sample_packs()

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
        prefs = "preferences.yaml"

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

    ###########################################################################

    @property
    def state(self) -> State:
        return self._history[-1]
