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
from PyQt6.QtCore import QObject, pyqtSignal

# Package imports
from smw_music import SmwMusicException, __version__
from smw_music.music_xml import MusicXmlException
from smw_music.music_xml.echo import EchoCh
from smw_music.music_xml.instrument import (
    Artic,
    Dynamics,
    GainMode,
    SampleSource,
)
from smw_music.music_xml.song import Song
from smw_music.ui.sample import SamplePack
from smw_music.ui.state import PreferencesState, State

###############################################################################
# Private Function Definitions
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
# API Class Definitions
###############################################################################


class Model(QObject):  # pylint: disable=too-many-public-methods
    state_changed = pyqtSignal(State)
    instruments_changed = pyqtSignal(list)
    sample_packs_changed = pyqtSignal(dict)

    mml_generated = pyqtSignal(str)  # arguments=['mml']
    response_generated = pyqtSignal(
        bool, str, str
    )  # arguments=["error", "title", "response"]

    song: Song | None
    preferences: PreferencesState
    _history: list[State]
    _undo_level: int
    _sample_packs: dict[str, SamplePack]
    _project_path: Path | None
    _project_name: str | None

    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self) -> None:
        super().__init__()
        self.song = None
        self.preferences = PreferencesState(Path(""), {}, Path(""))
        self._history = [State()]
        self._undo_level = 0

        self._project_path = None
        self._project_name = None

    ###########################################################################
    # API method definitions
    ###########################################################################

    def create_project(
        self, path: Path, project_name: str | None = None
    ) -> None:
        self._project_path = path
        self._project_name = project_name or path.name

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

        with zipfile.ZipFile(str(self.preferences.amk_fname), "r") as zobj:
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

        self._update_state(
            mml_fname=str(
                self._project_path / "music" / f"{self._project_name}.txt"
            )
        )

        self.on_save()

    ###########################################################################

    def reinforce_state(self) -> None:
        self._update_instruments()
        self.state_changed.emit(self.state)

    ###########################################################################

    def update_preferences(self, preferences: PreferencesState) -> None:
        prefs_dict = {
            "beer": __version__,
            "amk": {"path": str(preferences.amk_fname)},
            "spcplay": {"path": str(preferences.spcplay_fname)},
            "sample_packs": {
                name: {"path": str(path)}
                for name, path in preferences.sample_packs.items()
            },
        }

        with open(self.prefs_fname, "w", encoding="utf8") as fobj:
            yaml.safe_dump(prefs_dict, fobj)

        self._load_prefs()

    ###########################################################################

    def start(self) -> None:
        if self.prefs_fname.exists():
            self._load_prefs()
        self.reinforce_state()

    ###########################################################################
    # API slot definitions
    ###########################################################################

    def on_artic_length_changed(self, artic: Artic, val: int | str) -> None:
        max_len = 7
        artics = dict(self.state.inst.artics)
        artics[artic] = replace(
            artics[artic], length=_parse_setting(val, max_len)
        )
        self._update_inst_state(artics=artics)

    ###########################################################################

    def on_artic_volume_changed(self, artic: Artic, val: int | str) -> None:
        max_vol = 15
        artics = dict(self.state.inst.artics)
        artics[artic] = replace(
            artics[artic], volume=_parse_setting(val, max_vol)
        )
        self._update_inst_state(artics=artics)

    ###########################################################################

    def on_attack_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 15)
        self._update_inst_state(attack_setting=setting)

    ###########################################################################

    def on_brr_fname_changed(self, fname: str) -> None:
        self._update_inst_state(brr_fname=Path(fname))

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
        setting = _parse_setting(val)
        if self.state.inst.dyn_interpolate:
            self._interpolate(level, setting)
        else:
            dynamics = dict(self.state.inst.dynamics)
            dynamics[level] = setting
            self._update_inst_state(dynamics=dynamics)

    ###########################################################################

    def on_echo_en_changed(self, chan: EchoCh, state: bool) -> None:
        enables = self.state.echo.enables.copy()
        if state:
            enables.add(chan)
        else:
            enables.remove(chan)
        self._update_echo_state(enables=enables)

    ###########################################################################

    def on_echo_feedback_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 128) / 128
        self._update_echo_state(fb_mag=setting)

    ###########################################################################

    def on_echo_feedback_surround_changed(self, state: bool) -> None:
        self._update_echo_state(fb_inv=state)

    ###########################################################################

    def on_echo_left_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 128) / 128
        self._update_echo_state(vol_mag=(setting, self.state.echo.vol_mag[1]))

    ###########################################################################

    def on_echo_left_surround_changed(self, state: bool) -> None:
        self._update_echo_state(vol_inv=(state, self.state.echo.vol_inv[1]))

    ###########################################################################

    def on_echo_right_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 128) / 128
        self._update_echo_state(vol_mag=(self.state.echo.vol_mag[0], setting))

    ###########################################################################

    def on_echo_right_surround_changed(self, state: bool) -> None:
        self._update_echo_state(vol_inv=(self.state.echo.vol_inv[0], state))

    ###########################################################################

    def on_echo_delay_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 15)
        self._update_echo_state(delay=setting)

    ###########################################################################

    def on_filter_0_toggled(self, state: bool) -> None:
        self._update_echo_state(fir_filt=0 if state else 1)

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

    def on_generate_and_play_clicked(self) -> None:
        self.on_generate_mml_clicked(False)
        self.on_generate_spc_clicked(False)
        self.on_play_spc_clicked()

    ###########################################################################

    def on_generate_mml_clicked(self, report: bool = True) -> None:
        title = "MML Generation"
        error = True
        fname = self.state.mml_fname
        if self.song is None:
            msg = "Song not loaded"
        else:
            try:
                if os.path.exists(fname):
                    shutil.copy2(fname, f"{fname}.bak")

                # Update the instruments in the song
                # Applying this here means we can reload
                self.song.instruments = self.state.instruments

                mml = self.song.to_mml_file(
                    fname,
                    self.state.global_legato,
                    self.state.loop_analysis,
                    self.state.superloop_analysis,
                    self.state.measure_numbers,
                    True,
                    self.state.echo,
                    True,
                )
                self.mml_generated.emit(mml)
            except MusicXmlException as e:
                msg = str(e)
            else:
                error = False
                msg = "Done"
        if report:
            self.response_generated.emit(error, title, msg)

    ###########################################################################

    def on_generate_spc_clicked(self, report: bool = True) -> None:
        assert self._project_path is not None

        samples_path = self._project_path / "samples"
        for inst in self.state.instruments:
            if inst.sample_source == SampleSource.BRR:
                shutil.copy2(inst.brr_fname, samples_path)
            if inst.sample_source == SampleSource.SAMPLEPACK:
                target = (
                    samples_path / inst.pack_sample[0] / inst.pack_sample[1]
                )
                os.makedirs(target.parents[0], exist_ok=True)
                with open(target, "wb") as fobj:
                    fobj.write(
                        self._sample_packs[inst.pack_sample[0]][
                            inst.pack_sample[1]
                        ].data
                    )

        # TODO: support OSX and windows
        msg = subprocess.check_output(  # nosec B603, B607
            ["sh", "convert.sh"], cwd=self._project_path
        )
        if report:
            self.response_generated.emit(False, "SPC Generated", msg.decode())

    ###########################################################################

    def on_global_volume_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(global_volume=setting)

    ###########################################################################

    def on_global_legato_changed(self, state: bool) -> None:
        self._update_state(global_legato=state)

    ###########################################################################

    def on_instrument_changed(self, index: int) -> None:
        self._update_state(instrument_idx=index)

    ###########################################################################

    def on_interpolate_changed(self, state: bool) -> None:
        self._update_inst_state(dyn_interpolate=state)

    ###########################################################################

    def on_load(self, fname: Path) -> None:
        with open(fname, "r", encoding="utf8") as fobj:
            contents = yaml.unsafe_load(fobj)

        self._undo_level = 0
        self._history = [replace(contents["state"])]
        self._project_name = contents["song"]
        self._project_path = fname.parent
        self.song = Song.from_music_xml(self.state.musicxml_fname)
        self.song.instruments[:] = self.state.instruments

        self.reinforce_state()

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

    def on_musicxml_fname_changed(self, fname: str) -> None:
        try:
            self.song = Song.from_music_xml(fname)
        except MusicXmlException as e:
            self.response_generated.emit(True, "Song load", str(e))
        else:
            self.state.instruments = self.song.instruments
            self._update_instruments()
        self._update_state(musicxml_fname=fname)

    ###########################################################################

    def on_mute_changed(self, state: bool) -> None:
        self._update_inst_state(mute=state)

    ###########################################################################

    def on_octave_changed(self, octave: int) -> None:
        self._update_inst_state(octave=octave)

    ###########################################################################

    def on_pack_sample_changed(self, item_id: tuple[str, Path]) -> None:
        self._update_inst_state(pack_sample=item_id)
        if self.state.inst.sample_source == SampleSource.SAMPLEPACK:
            self._load_sample_settings(item_id)

    ###########################################################################

    def on_pack_sample_selected(self, state: bool) -> None:
        if state:
            self._update_inst_state(sample_source=SampleSource.SAMPLEPACK)
            sample = self.state.inst.pack_sample
            if sample[0]:
                self._load_sample_settings(sample)

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
                args=(
                    ["wine", str(self.preferences.spcplay_fname), spc_name],
                ),
            ).start()

    ###########################################################################

    def on_redo_clicked(self) -> None:
        if self._undo_level > 0:
            self._undo_level -= 1
            self.state_changed.emit(self.state)

    ###########################################################################

    def on_reload_musicxml_clicked(self) -> None:
        self.song = Song.from_music_xml(self.state.musicxml_fname)

        instruments = {inst.name: inst for inst in self.state.instruments}

        for n, instrument in enumerate(self.song.instruments):
            if instrument.name in instruments:
                self.song.instruments[n] = instruments[instrument.name]

        self._update_instruments()

    ###########################################################################

    def on_save(self) -> None:
        contents = {
            "version": __version__,
            "song": self._project_name,
            "state": self.state,
        }

        fname = self._project_path / (self._project_name + ".prj")
        with open(fname, "w", encoding="utf8") as fobj:
            yaml.dump(contents, fobj)

    ###########################################################################

    def on_select_adsr_mode_selected(self, state: bool) -> None:
        self._update_inst_state(adsr_mode=state)

    ###########################################################################

    def on_solo_changed(self, state: bool) -> None:
        self._update_inst_state(solo=state)

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

    #    def save_as(self, fname: str) -> None:
    #        self._project_file = Path(fname)
    #        self.save()
    #
    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _interpolate(self, level: Dynamics, setting: int) -> None:
        inst = self.state.inst
        dyns = sorted(inst.dynamics_present)
        dynamics = dict(inst.dynamics)

        min_dyn = min(dyns)
        max_dyn = max(dyns)

        min_setting = dynamics[min_dyn]
        max_setting = dynamics[max_dyn]

        # Clip the setting
        if level != min_dyn:
            setting = max(min_setting, setting)
        if level != max_dyn:
            setting = min(max_setting, setting)

        for dyn in dyns:
            if dyn == level:
                val = setting
            elif dyn in [min_dyn, max_dyn]:
                continue
            elif dyn < level:
                numer = 1 + sum(dyn < x < level for x in dyns)
                denom = 1 + sum(min_dyn < x < level for x in dyns)
                val = round(
                    min_setting
                    + (setting - min_setting) * (denom - numer) / denom
                )
            else:  # dyn > level
                numer = 1 + sum(level < x < dyn for x in dyns)
                denom = 1 + sum(level < x < max_dyn for x in dyns)
                val = round(setting + (max_setting - setting) * numer / denom)

            dynamics[dyn] = val

        self._update_inst_state(dynamics=dynamics)

    ###########################################################################

    def _load_prefs(self) -> None:
        with open(self.prefs_fname, "r", encoding="utf8") as fobj:
            prefs = yaml.safe_load(fobj)

        self.preferences.amk_fname = Path(prefs["amk"]["path"])
        self.preferences.spcplay_fname = Path(prefs["spcplay"]["path"])
        self.preferences.sample_packs = {
            name: Path(pack["path"])
            for name, pack in prefs["sample_packs"].items()
        }

        self._load_sample_packs()

    ###########################################################################

    def _load_sample_packs(self) -> None:

        self._sample_packs = {}

        for name, path in self.preferences.sample_packs.items():
            try:
                self._sample_packs[name] = SamplePack(path)

            except FileNotFoundError:
                self.response_generated.emit(
                    True,
                    "Error loading sample pack",
                    f"Could not open sample pack {name} at {path}",
                )

        self.sample_packs_changed.emit(self._sample_packs)

    ###########################################################################

    def _load_sample_settings(self, item_id: tuple[str, Path]) -> None:
        pack, sample_path = item_id
        params = self._sample_packs[pack][sample_path].params

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
        self._update_inst_state(**new_state)

    ###########################################################################

    def _rollback_undo(self) -> None:
        while self._undo_level:
            self._history.pop()
            self._undo_level -= 1

    ###########################################################################

    def _update_echo_state(self, **kwargs) -> None:
        new_echo = replace(self.state.echo, **kwargs)
        self._update_state(echo=new_echo)

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

    def _update_instruments(self) -> None:
        if song := self.song:
            self.instruments_changed.emit([x.name for x in song.instruments])

    ###########################################################################

    def _update_state(self, **kwargs) -> None:
        new_state = replace(self.state, **kwargs)
        if new_state != self.state:
            self._rollback_undo()

            self._history.append(new_state)
            self.state_changed.emit(new_state)

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def prefs_fname(self) -> Path:
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
