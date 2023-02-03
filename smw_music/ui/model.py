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
import threading
import zipfile
from dataclasses import replace
from pathlib import Path

# Library imports
import yaml
from mako.template import Template  # type: ignore
from PyQt6.QtCore import QModelIndex, QObject, Qt, pyqtSignal
from PyQt6.QtGui import QStandardItem, QStandardItemModel

# Package imports
from smw_music import SmwMusicException, __version__
from smw_music.music_xml import MusicXmlException
from smw_music.music_xml.echo import EchoConfig
from smw_music.music_xml.instrument import (
    Artic,
    Dynamics,
    GainMode,
    SampleSource,
)
from smw_music.music_xml.song import Song
from smw_music.ramfs import RamFs
from smw_music.ui.sample import SampleParams, extract_sample_pack
from smw_music.ui.state import EchoCh, State

###############################################################################
# Private Function Definitions
###############################################################################


def _add_brr_to_model(
    top_item: QStandardItem,
    parents: dict[tuple[str, ...], QStandardItem],
    fname: tuple[str, ...],
    params: SampleParams,
) -> None:
    parent = top_item
    for n, path_item in enumerate(fname):
        partial_path = fname[: (n + 1)]
        try:
            parent = parents[partial_path]
        except KeyError:
            item = QStandardItem(path_item)
            parents[partial_path] = item
            parent.appendRow(item)
            parent = item

    # Set the data of the leaf to the sample parameters
    item.setData(params, Qt.ItemDataRole.UserRole)


###############################################################################


def _add_sample_pack_to_model(
    model: QStandardItemModel, pack: str, path: Path
) -> None:

    parents: dict[tuple[str, ...], QStandardItem] = {}

    extracted_pack = extract_sample_pack(path)

    # Add the pack as a top-level item
    top_item = QStandardItem(pack)
    model.appendRow(top_item)

    for sample_name, params in extracted_pack.items():
        _add_brr_to_model(top_item, parents, sample_name, params)


###############################################################################


def _parse_setting(val: int | str, maxval: int = 255) -> int:
    if isinstance(val, int):
        return val

    val = val.strip()
    if val[-1] == "%":
        return int(maxval * float(val[:-1]) / 100)
    if val[0] == "$":
        return int(val[1:], 16)
    return int(float(val))


###############################################################################


def _dyn_to_str(dyn: Dynamics) -> str:
    lut = {
        Dynamics.PPPP: "PPPP",
        Dynamics.PPP: "PPP",
        Dynamics.PP: "PP",
        Dynamics.P: "P",
        Dynamics.MP: "MP",
        Dynamics.MF: "MF",
        Dynamics.F: "F",
        Dynamics.FF: "FF",
        Dynamics.FFF: "FFF",
        Dynamics.FFFF: "FFFF",
    }
    return lut[dyn]


###############################################################################


def _str_to_dyn(dyn: str) -> Dynamics:
    lut = {
        "PPPP": Dynamics.PPPP,
        "PPP": Dynamics.PPP,
        "PP": Dynamics.PP,
        "P": Dynamics.P,
        "MP": Dynamics.MP,
        "MF": Dynamics.MF,
        "F": Dynamics.F,
        "FF": Dynamics.FF,
        "FFF": Dynamics.FFF,
        "FFFF": Dynamics.FFFF,
    }
    return lut[dyn]


###############################################################################
# API Class Definitions
###############################################################################


class Model(QObject):  # pylint: disable=too-many-public-methods
    state_changed = pyqtSignal(State)
    instruments_changed = pyqtSignal(list)
    sample_packs_changed = pyqtSignal(list)

    mml_generated = pyqtSignal(str)  # arguments=['mml']
    response_generated = pyqtSignal(
        bool, str, str
    )  # arguments=["error", "title", "response"]

    song: Song | None
    sample_packs_model: QStandardItemModel
    _history: list[State]
    _undo_level: int
    _amk_path: Path | None
    _sample_packs: dict[str, dict[str, str]] | None
    _spcplay_path: Path | None
    _project_file: Path | None
    _project_name: str | None

    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self) -> None:
        super().__init__()
        self.song = None
        self.sample_packs_model = QStandardItemModel()
        self._history = [State()]
        self._undo_level = 0

        self._load_prefs()

    ###########################################################################
    # API method definitions
    ###########################################################################

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

    def load(self, fname: str) -> None:
        with open(fname, "r", encoding="utf8") as fobj:
            contents = yaml.safe_load(fobj)

        self._project_name = contents["song"]
        self._project_file = Path(fname)

    ###########################################################################

    def reinforce_state(self) -> None:
        self.state_changed.emit(self.state)

    ###########################################################################
    # API slot  definitions
    ###########################################################################

    def on_artic_length_changed(self, artic: Artic, val: int | str) -> None:
        max_len = 7
        artics = dict(self.state.inst.artic_settings)
        artics[artic] = replace(
            artics[artic], length=_parse_setting(val, max_len)
        )
        self._update_inst_state(artic_settings=artics)

    ###########################################################################

    def on_artic_volume_changed(self, artic: Artic, val: int | str) -> None:
        max_vol = 15
        artics = dict(self.state.inst.artic_settings)
        artics[artic] = replace(
            artics[artic], volume=_parse_setting(val, max_vol)
        )
        self._update_inst_state(artic_settings=artics)

    ###########################################################################

    def on_attack_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 15)
        self._update_inst_state(attack_setting=setting)

    ###########################################################################

    def on_brr_fname_changed(self, fname: str) -> None:
        self._update_inst_state(brr_fname=fname)

    ###########################################################################

    def on_brr_sample_selected(self, state: bool) -> None:
        if state:
            self._update_inst_state(sample_source=SampleSource.BRR)

    ###########################################################################

    def on_brr_setting_changed(self, val: str) -> None:
        self._update_inst_state(brr_setting=val)

    ###########################################################################

    def on_builtin_sample_changed(self, index: int) -> None:
        self._update_inst_state(builtin_sample_index=index)

    ###########################################################################

    def on_builtin_sample_selected(self, state: bool) -> None:
        if state:
            self._update_inst_state(sample_source=SampleSource.BUILTIN)

    ###########################################################################

    def on_decay_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 7)
        self._update_inst_state(decay_setting=setting)

    ###########################################################################

    def on_dynamics_changed(self, level: Dynamics, val: int | str) -> None:
        dynamics = dict(self.state.inst.dynamics_settings)
        dynamics[level] = _parse_setting(val)
        self._update_inst_state(dynamics_settings=dynamics)

    ###########################################################################

    def on_echo_en_changed(self, chan: EchoCh, state: bool) -> None:
        echo_enable = dict(self.state.echo_enable)
        echo_enable[chan] = state
        self._update_state(echo_enable=echo_enable)

    ###########################################################################

    def on_echo_feedback_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(echo_feedback_setting=setting)

    ###########################################################################

    def on_echo_feedback_surround_changed(self, state: bool) -> None:
        # TODO
        pass

    ###########################################################################

    def on_echo_left_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(echo_left_setting=setting)

    ###########################################################################

    def on_echo_left_surround_changed(self, state: bool) -> None:
        # TODO
        pass

    ###########################################################################

    def on_echo_right_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(echo_right_setting=setting)

    ###########################################################################

    def on_echo_right_surround_changed(self, state: bool) -> None:
        # TODO
        pass

    ###########################################################################

    def on_echo_delay_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(echo_delay_setting=setting)

    ###########################################################################

    def on_filter_0_toggled(self, state: bool) -> None:
        self._update_state(echo_filter0=state)

    ###########################################################################

    def on_gain_declin_selected(self, state: bool) -> None:
        if state:
            self._update_inst_state(gain_mode=GainMode.DECLIN)

    ###########################################################################

    def on_gain_decexp_selected(self, state: bool) -> None:
        if state:
            self._update_inst_state(gain_mode=GainMode.DECEXP)

    ###########################################################################

    def on_gain_direct_selected(self, state: bool) -> None:
        if state:
            self._update_inst_state(gain_mode=GainMode.DIRECT)

    ###########################################################################

    def on_gain_incbent_selected(self, state: bool) -> None:
        if state:
            self._update_inst_state(gain_mode=GainMode.INCBENT)

    ###########################################################################

    def on_gain_inclin_selected(self, state: bool) -> None:
        if state:
            self._update_inst_state(gain_mode=GainMode.INCLIN)

    ###########################################################################

    def on_gain_changed(self, val: int | str) -> None:
        limit = 127 if self.state.inst.gain_mode == GainMode.DIRECT else 31
        setting = _parse_setting(val, limit)
        self._update_inst_state(gain_setting=setting)

    ###########################################################################

    def on_generate_mml_clicked(self) -> None:
        pass

    ###########################################################################

    def on_generate_spc_clicked(self) -> None:
        # TODO: support OSX and windows
        subprocess.call(  # nosec B603, B607
            ["sh", "convert.sh"], cwd=self._project_path
        )

    ###########################################################################

    def on_global_volume_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(global_volume=setting)

    ###########################################################################

    def on_global_legato_changed(self, state: bool) -> None:
        self._update_state(global_legato=state)

    ###########################################################################

    def on_interpolate_changed(self, state: bool) -> None:
        self._update_inst_state(dyn_interpolate=state)

    ###########################################################################

    def on_loop_analysis_changed(self, enabled: bool) -> None:
        self._update_state(loop_analysis=enabled)

    ###########################################################################

    def on_measure_numbers_changed(self, enabled: bool) -> None:
        self._update_state(measure_numbers=enabled)

    ###########################################################################

    def on_mml_fname_changed(self, fname: str) -> None:
        self._update_state(mml_fname=fname)

    ###########################################################################

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
                    self.state.global_legato,
                    self.state.loop_analysis,
                    self.state.superloop_analysis,
                    self.state.measure_numbers,
                    True,
                    echo,
                    True,
                    True,
                )
                self.mml_generated.emit(mml)
            except MusicXmlException as e:
                msg = str(e)
            else:
                error = False
                msg = "Done"
        self.response_generated.emit(error, title, msg)

    ###########################################################################

    def on_musicxml_fname_changed(self, fname: str) -> None:
        try:
            self.song = Song.from_music_xml(fname)
        except MusicXmlException as e:
            self.response_generated.emit(True, "Song load", str(e))
        else:
            self.instruments_changed.emit(
                [x.name for x in self.song.instruments]
            )
        self._update_state(musicxml_fname=fname)

    ###########################################################################

    def on_pack_sample_changed(self, index: QModelIndex) -> None:
        if self.state.inst.sample_source == SampleSource.SAMPLEPACK:
            self._load_sample_settings(index)

    ###########################################################################

    def on_pack_sample_selected(self, state: bool) -> None:
        if state:
            self._update_inst_state(sample_source=SampleSource.SAMPLEPACK)

    ###########################################################################

    def on_pan_enable_changed(self, state: bool) -> None:
        self._update_inst_state(pan_enabled=state)

    ###########################################################################

    def on_pan_setting_changed(self, val: int) -> None:
        self._update_inst_state(pan_setting=val)

    ###########################################################################

    def on_play_spc_clicked(self) -> None:
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

    def on_redo_clicked(self) -> None:
        if self._undo_level > 0:
            self._undo_level -= 1
            self.state_changed.emit(self.state)

    ###########################################################################

    def on_select_adsr_mode_selected(self, state: bool) -> None:
        self._update_inst_state(adsr_mode=state)

    ###########################################################################

    def on_subtune_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_inst_state(subtune_setting=setting)

    ###########################################################################

    def on_superloop_analysis_changed(self, enabled: bool) -> None:
        self._update_state(superloop_analysis=enabled)

    ###########################################################################

    def on_sus_level_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 7)
        self._update_inst_state(sus_level_setting=setting)

    ###########################################################################

    def on_sus_rate_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 31)
        self._update_inst_state(sus_rate_setting=setting)

    ###########################################################################

    def on_tune_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_inst_state(tune_setting=setting)

    ###########################################################################

    def on_undo_clicked(self) -> None:
        if self._undo_level < len(self._history) - 1:
            self._undo_level += 1
            self.state_changed.emit(self.state)

    ###########################################################################

    def save(self) -> None:
        contents = {
            "version": __version__,
            "song": self._project_name,
            "samples": "",
        }

        if self._project_file is not None:
            with open(self._project_file, "w", encoding="utf8") as fobj:
                yaml.dump(contents, fobj)

    ###########################################################################

    def save_as(self, fname: str) -> None:
        self._project_file = Path(fname)
        self.save()

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _init_prefs(self) -> None:
        pass

    ###########################################################################

    def _interpolate(self, dyn_str: str, level: int) -> None:
        inst = self.state.inst
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

    def _load_sample_packs(self) -> None:
        assert self._sample_packs is not None  # nosec 703

        for pack_name, pack in self._sample_packs.items():
            _add_sample_pack_to_model(
                self.sample_packs_model, pack_name, Path(pack["path"])
            )

    ###########################################################################

    def _load_sample_settings(self, index: QModelIndex) -> None:
        params: SampleParams | None = index.data(Qt.ItemDataRole.UserRole)
        if params is not None:
            new_state = {
                "attack_setting": params.attack,
                "decay_setting": params.decay,
                "sus_level_setting": params.sustain_level,
                "sus_rate_setting": params.sustain_rate,
                "adsr_mode": params.adsr_mode,
                "gain_mode": params.gain_mode,
                "gain_setting": params.gain,
                "tune_setting": params.tuning,
                "subtune_setting": params.subtuning,
            }
            print("update sample settings")
            self._update_inst_state(**new_state)

    ###########################################################################

    def _rollback_undo(self) -> None:
        while self._undo_level:
            self._history.pop()
            self._undo_level -= 1

    ###########################################################################

    def _update_inst_state(self, **kwargs) -> None:
        try:
            new_inst = replace(self.state.inst, **kwargs)
        except TypeError:
            new_inst = replace(self.state.inst)
            for key, val in kwargs.items():
                setattr(new_inst, key, val)

        if new_inst != self.state.inst:
            self._rollback_undo()

            new_state = replace(self.state)
            new_state.inst = new_inst
            self._history.append(new_state)
            self.state_changed.emit(new_state)

    ###########################################################################

    def _update_state(self, **kwargs) -> None:
        new_state = replace(self.state, **kwargs)
        if new_state != self.state:
            self._rollback_undo()

            self._history.append(new_state)
            self.state_changed.emit(new_state)

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
        return self._history[-1 - self._undo_level]
