# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
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
from contextlib import suppress
from copy import deepcopy
from dataclasses import replace
from glob import glob
from pathlib import Path, PurePosixPath
from random import choice

# Library imports
import yaml
from mako.template import Template  # type: ignore
from PyQt6.QtCore import QObject, pyqtSignal

# Package imports
from smw_music import SmwMusicException, __version__
from smw_music.music_xml import MusicXmlException
from smw_music.music_xml.echo import EchoCh, EchoConfig
from smw_music.music_xml.instrument import (
    Artic,
    ArticSetting,
    Dynamics,
    GainMode,
    InstrumentConfig,
    SampleSource,
)
from smw_music.music_xml.song import Song
from smw_music.ui.quotes import ashtley, quotes
from smw_music.ui.sample import SamplePack
from smw_music.ui.save import load, save
from smw_music.ui.state import PreferencesState, State

###############################################################################
# Private Function Definitions
###############################################################################


def _endis(state: bool) -> str:
    return "enabled" if state else "disabled"


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
    state_changed = pyqtSignal(
        State, bool
    )  # arguments=['state', 'update_instruments']
    preferences_changed = pyqtSignal(
        bool, bool, bool, dict
    )  # arguments = ['advanced_enabled', 'amk_valid', 'spcplayer_valid', 'sample_packs']
    instruments_changed = pyqtSignal(list)
    recent_projects_updated = pyqtSignal(list)

    mml_generated = pyqtSignal(str)  # arguments=['mml']
    status_updated = pyqtSignal(str)  # arguments=['message']
    response_generated = pyqtSignal(
        bool, str, str
    )  # arguments=["error", "title", "response"]

    song: Song | None
    preferences: PreferencesState
    _history: list[State]
    _undo_level: int
    _sample_packs: dict[str, SamplePack]
    _project_path: Path | None

    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self) -> None:
        super().__init__()
        self.song = None
        self.preferences = PreferencesState()
        self._history = [State()]
        self._undo_level = 0
        self._sample_packs = {}
        self._project_path = None

        os.makedirs(self.config_dir, exist_ok=True)

    ###########################################################################
    # API method definitions
    ###########################################################################

    def create_project(
        self, path: Path, project_name: str | None = None
    ) -> None:
        self._project_path = path
        if project_name is None:
            project_name = path.name

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
            script = tmpl.render(project=project_name)
            target = path / tmpl_name

            with open(target, "w", encoding="utf8") as fobj:
                fobj.write(script)

            os.chmod(target, os.stat(target).st_mode | stat.S_IXUSR)

        self._update_state(
            project_name=project_name,
            mml_fname=str(
                self._project_path / "music" / f"{project_name}.txt"
            ),
        )

        # TODO: Unify this project path with what's used in on_save
        self._append_recent_project(path / (project_name + ".prj"))
        self._update_status(f"Created project {project_name}")
        self.on_save()

    ###########################################################################

    def close_project(self) -> None:
        self._project_path = None
        self._update_state(project_name=None)
        self._update_status("Project closed")

    ###########################################################################

    def reinforce_state(self) -> None:
        self._signal_state_change(update_instruments=True, state_change=False)

    ###########################################################################

    def start(self) -> None:
        self._load_prefs()

        self.recent_projects_updated.emit(self.recent_projects)
        self.reinforce_state()

        quote: tuple[str, str] = choice(quotes)  # nosec: B311
        self._update_status(f"{quote[1]}: {quote[0]}")

    ###########################################################################

    def update_preferences(self, preferences: PreferencesState) -> None:
        prefs_dict = {
            "beer": __version__,
            "amk": {"path": str(preferences.amk_fname)},
            "spcplay": {"path": str(preferences.spcplay_fname)},
            "sample_packs": {"path": str(preferences.sample_pack_dname)},
            "advanced": preferences.advanced_mode,
        }

        with open(self.prefs_fname, "w", encoding="utf8") as fobj:
            yaml.safe_dump(prefs_dict, fobj)

        self._load_prefs()

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
        self._update_status(f"{artic} length set to {val}")

    ###########################################################################

    def on_artic_volume_changed(self, artic: Artic, val: int | str) -> None:
        max_vol = 15
        artics = dict(self.state.inst.artics)
        artics[artic] = replace(
            artics[artic], volume=_parse_setting(val, max_vol)
        )
        self._update_inst_state(artics=artics)
        self._update_status(f"{artic} volume set to {val}")

    ###########################################################################

    def on_attack_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 15)
        self._update_inst_state(attack_setting=setting)
        self._update_status(f"Attack set to {setting}")

    ###########################################################################

    def on_brr_fname_changed(self, fname: str) -> None:
        self._update_inst_state(brr_fname=Path(fname))
        self._update_status(f"BRR set to {fname}")

    ###########################################################################

    def on_brr_sample_selected(self, state: bool) -> None:
        if state:
            self._update_inst_state(sample_source=SampleSource.BRR)
            self._update_status("Sample source set to BRR")

    ###########################################################################

    def on_brr_setting_changed(self, val: str) -> None:
        self._update_inst_state(brr_setting=val)
        self._update_status(f"BRR setting changed to {val}")

    ###########################################################################

    def on_builtin_sample_changed(self, index: int) -> None:
        self._update_inst_state(builtin_sample_index=index)
        self._update_status(f"Builtin sample {index} selected")

    ###########################################################################

    def on_builtin_sample_selected(self, state: bool) -> None:
        if state:
            self._update_inst_state(sample_source=SampleSource.BUILTIN)
            self._update_status("Sample source set to builtin")

    ###########################################################################

    def on_decay_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 7)
        self._update_inst_state(decay_setting=setting)
        self._update_status(f"Decay set to {setting}")

    ###########################################################################

    def on_dynamics_changed(self, level: Dynamics, val: int | str) -> None:
        setting = _parse_setting(val)
        if self.state.inst.dyn_interpolate:
            self._interpolate(level, setting)
        else:
            dynamics = dict(self.state.inst.dynamics)
            dynamics[level] = setting
            self._update_inst_state(dynamics=dynamics)

        self._update_status(f"Dynamics {level} set to {setting}")

    ###########################################################################

    def on_echo_en_changed(self, chan: EchoCh, state: bool) -> None:
        enables = self.state.echo.enables.copy()
        if state:
            enables.add(chan)
        else:
            enables.remove(chan)
        self._update_echo_state(enables=enables)
        self._update_status(f"Echo {str(chan)} {_endis(state)}")

    ###########################################################################

    def on_echo_feedback_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 128) / 128
        self._update_echo_state(fb_mag=setting)
        self._update_status(f"Echo feedback magnitude set to {setting}")

    ###########################################################################

    def on_echo_feedback_surround_changed(self, state: bool) -> None:
        self._update_echo_state(fb_inv=state)
        self._update_status(f"Echo feedback surround {_endis(state)}")

    ###########################################################################

    def on_echo_left_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 128) / 128
        self._update_echo_state(vol_mag=(setting, self.state.echo.vol_mag[1]))
        self._update_status(f"Echo left channel magnitude set to {setting}")

    ###########################################################################

    def on_echo_left_surround_changed(self, state: bool) -> None:
        self._update_echo_state(vol_inv=(state, self.state.echo.vol_inv[1]))
        self._update_status(f"Echo left channel surround {_endis(state)}")

    ###########################################################################

    def on_echo_right_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 128) / 128
        self._update_echo_state(vol_mag=(self.state.echo.vol_mag[0], setting))
        self._update_status(f"Echo right channel magnitude set to {setting}")

    ###########################################################################

    def on_echo_right_surround_changed(self, state: bool) -> None:
        self._update_echo_state(vol_inv=(self.state.echo.vol_inv[0], state))
        self._update_status(f"Echo right channel surround {_endis(state)}")

    ###########################################################################

    def on_echo_delay_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 15)
        self._update_echo_state(delay=setting)
        self._update_status(f"Echo delay changed to {val}")

    ###########################################################################

    def on_filter_0_toggled(self, state: bool) -> None:
        self._update_echo_state(fir_filt=0 if state else 1)
        self._update_status(f"Echo filter set to {0 if state else 1}")

    ###########################################################################

    def on_gain_declin_selected(self, state: bool) -> None:
        if state:
            self._update_inst_state(
                gain_mode=GainMode.DECLIN,
                gain_setting=min(31, self.state.inst.gain_setting),
            )
            self._update_status("Decreasing linear envelope selected")

    ###########################################################################

    def on_gain_decexp_selected(self, state: bool) -> None:
        if state:
            self._update_inst_state(
                gain_mode=GainMode.DECEXP,
                gain_setting=min(31, self.state.inst.gain_setting),
            )
            self._update_status("Decreasing exponential envelope selected")

    ###########################################################################

    def on_gain_direct_selected(self, state: bool) -> None:
        if state:
            self._update_inst_state(gain_mode=GainMode.DIRECT)
            self._update_status("Direct gain envelope selected")

    ###########################################################################

    def on_gain_incbent_selected(self, state: bool) -> None:
        if state:
            self._update_inst_state(
                gain_mode=GainMode.INCBENT,
                gain_setting=min(31, self.state.inst.gain_setting),
            )
            self._update_status("Increasing bent envelope selected")

    ###########################################################################

    def on_gain_inclin_selected(self, state: bool) -> None:
        if state:
            self._update_inst_state(
                gain_mode=GainMode.INCLIN,
                gain_setting=min(31, self.state.inst.gain_setting),
            )
            self._update_status("Increasing linear envelope selected")

    ###########################################################################

    def on_gain_changed(self, val: int | str) -> None:
        # TODO: Unify this 31 with the others
        limit = 127 if self.state.inst.gain_mode == GainMode.DIRECT else 31
        setting = _parse_setting(val, limit)
        self._update_inst_state(gain_setting=setting)
        self._update_status("Gain setting changed to {setting}")

    ###########################################################################

    def on_game_name_changed(self, val: str) -> None:
        self._update_state(game=val)
        self._update_status(f"Game name set to {val}")

    ###########################################################################

    def on_generate_and_play_clicked(self) -> None:
        self._update_status("SPC generated and played")
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
            self.mml_generated.emit("\n".join(ashtley))
        else:
            assert self.state.project_name is not None  # nosec: B101

            try:
                if os.path.exists(fname):
                    shutil.copy2(fname, f"{fname}.bak")

                # Update the instruments in the song
                # Applying this here means we can reload
                self.song.instruments = self.state.instruments

                self.song.volume = self.state.global_volume
                if self.state.porter:
                    self.song.porter = self.state.porter
                if self.state.game:
                    self.song.game = self.state.game

                mml = self.song.to_mml_file(
                    fname,
                    self.state.global_legato,
                    self.state.loop_analysis,
                    self.state.superloop_analysis,
                    self.state.measure_numbers,
                    True,
                    self.state.echo if self.state.global_echo_enable else None,
                    True,
                    PurePosixPath(self.state.project_name),
                    self.state.solo_percussion,
                    self.state.mute_percussion,
                    self.state.start_measure,
                )
                self.mml_generated.emit(mml)
                self._update_status("MML generated")
            except MusicXmlException as e:
                msg = str(e)
            else:
                error = False
                msg = "Done"

        if report or error:
            self.response_generated.emit(error, title, msg)

    ###########################################################################

    def on_generate_spc_clicked(self, report: bool = True) -> None:
        assert self._project_path is not None  # nosec: B101
        assert self.state.project_name is not None  # nosec: B101

        error = False
        msg = ""

        if not os.path.exists(self.state.mml_fname):
            error = True
            msg = "MML not generated"
        else:
            samples_path = (
                self._project_path / "samples" / self.state.project_name
            )

            shutil.rmtree(samples_path, ignore_errors=True)

            for inst in self.state.instruments:
                if inst.sample_source == SampleSource.BRR:
                    shutil.copy2(inst.brr_fname, samples_path)
                if inst.sample_source == SampleSource.SAMPLEPACK:
                    pack_name, pack_path = inst.pack_sample
                    target = samples_path / pack_name / pack_path
                    os.makedirs(target.parents[0], exist_ok=True)
                    with open(target, "wb") as fobj:
                        try:
                            fobj.write(
                                self._sample_packs[pack_name][pack_path].data
                            )
                        except KeyError:
                            error = True
                            msg += f"Could not find sample pack {pack_name}\n"

            if not error:
                try:
                    msg = subprocess.check_output(  # nosec B603
                        self.convert,
                        cwd=self._project_path,
                        stderr=subprocess.STDOUT,
                        timeout=5,
                    ).decode()
                except subprocess.CalledProcessError as e:
                    error = True
                    msg = e.output.decode("utf8")
                except subprocess.TimeoutExpired:
                    error = True
                    msg = "Conversion timed out"

        if report or error:
            self.response_generated.emit(error, "SPC Generated", msg)
            self._update_status("SPC generated")

    ###########################################################################

    def on_global_echo_en_changed(self, state: bool) -> None:
        self._update_state(global_echo_enable=state)
        self._update_status(f"Echo {_endis(state)}")

    ###########################################################################

    def on_global_legato_changed(self, state: bool) -> None:
        self._update_state(global_legato=state)
        self._update_status(f"Global legato {_endis(state)}")

    ###########################################################################

    def on_global_volume_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(global_volume=setting)
        self._update_status(f"Global volume set to {setting}")

    ###########################################################################

    def on_instrument_changed(self, idx: int) -> None:
        self._update_state(instrument_idx=idx)
        inst = self.state.instruments[idx].name
        self._update_status(f"{inst} selected")

    ###########################################################################

    def on_interpolate_changed(self, state: bool) -> None:
        self._update_inst_state(dyn_interpolate=state)
        self._update_status(f"Dynamics interpolation {_endis(state)}")

    ###########################################################################

    def on_load(self, fname: Path) -> None:
        try:
            save_state = load(fname)
        except SmwMusicException as e:
            self.response_generated.emit(True, "Invalid save version", str(e))
        else:
            self._append_recent_project(fname)

            self._undo_level = 0
            self._history = [replace(save_state, instrument_idx=0)]
            self._project_path = fname.parent
            if musicxml := self.state.musicxml_fname:
                try:
                    self.song = Song.from_music_xml(musicxml)
                except MusicXmlException as e:
                    self.response_generated.emit(
                        True,
                        "Error loading score",
                        f"Could not open score {musicxml}: {str(e)}",
                    )
                else:
                    self.reinforce_state()
                    self._update_status(
                        f"Opened project {self.state.project_name}"
                    )
            else:
                self.song = None

    ###########################################################################

    def on_loop_analysis_changed(self, enabled: bool) -> None:
        self._update_state(loop_analysis=enabled)
        self._update_status(f"Loop analysis {_endis(enabled)}")

    ###########################################################################

    def on_measure_numbers_changed(self, enabled: bool) -> None:
        self._update_state(measure_numbers=enabled)
        self._update_status(f"Measure # reporting {_endis(enabled)}")

    ###########################################################################

    def on_mml_fname_changed(self, fname: str) -> None:
        self._update_state(mml_fname=fname)
        self._update_status(f"MML name set to {fname}")

    ###########################################################################

    def on_musicxml_fname_changed(self, fname: str) -> None:
        try:
            self.song = Song.from_music_xml(fname)
        except MusicXmlException as e:
            self.response_generated.emit(True, "Song load", str(e))
        else:
            self.state.instruments = self.song.instruments
        inst_idx = 0 if len(self.state.instruments) else None
        self._update_state(True, musicxml_fname=fname, instrument_idx=inst_idx)
        self._update_status(f"MusicXML name set to {fname}")

    ###########################################################################

    def on_mute_changed(self, idx: int, state: bool) -> None:
        self._update_inst_state(idx=idx, mute=state)
        inst = self.state.instruments[idx].name
        self._update_status(f"{inst} mute {_endis(state)}")

    ###########################################################################

    def on_mute_percussion_changed(self, state: bool) -> None:
        self._update_state(mute_percussion=state)
        self._update_status(f"Percussion mute {_endis(state)}")

    ###########################################################################

    def on_octave_changed(self, octave: int) -> None:
        self._update_inst_state(octave=octave)
        self._update_status(f"Octave set to {octave}")

    ###########################################################################

    def on_pack_sample_changed(self, item_id: tuple[str, Path]) -> None:
        self._update_inst_state(pack_sample=item_id)
        if self.state.inst.sample_source == SampleSource.SAMPLEPACK:
            self._load_sample_settings(item_id)
            self._update_status(
                f"Sample pack {item_id[0]}:{str(item_id[1])} selected"
            )

    ###########################################################################

    def on_pack_sample_selected(self, state: bool) -> None:
        if state:
            self._update_inst_state(sample_source=SampleSource.SAMPLEPACK)
            self._update_status("Sample source set to sample pack")
            sample = self.state.inst.pack_sample
            if sample[0]:
                self._load_sample_settings(sample)

    ###########################################################################

    def on_pan_enable_changed(self, state: bool) -> None:
        self._update_inst_state(pan_enabled=state)
        self._update_status(f"Pan {_endis(state)}")

    ###########################################################################

    def on_pan_invert_changed(self, left: bool, state: bool) -> None:
        pan_setting = list(self.state.inst.pan_invert)
        pan_setting[0 if left else 1] = state

        self._update_inst_state(pan_invert=(pan_setting[0], pan_setting[1]))
        self._update_status(
            f'Pan {"left" if left else "right"} inversion {_endis(state)}'
        )

    ###########################################################################

    def on_pan_setting_changed(self, val: int) -> None:
        self._update_inst_state(pan_setting=val)
        self._update_status(f"Pan changed to {val}")

    ###########################################################################

    def on_play_spc_clicked(self) -> None:
        path = self._project_path
        project = self.state.project_name

        assert path is not None  # nosec: B101
        assert project is not None  # nosec: B101

        spc_name = f"{project}.spc"
        spc_name = str(path / "SPCs" / spc_name)

        if not os.path.exists(spc_name):
            self.response_generated.emit(
                True, "SPC Play", "SPC file doesn't exist"
            )
        else:
            spc_name = f"{project}.spc"
            spc_name = str(path / "SPCs" / spc_name)

            # Handles linux and OSX, windows is covered on the next line
            args = ["wine", str(self.preferences.spcplay_fname), spc_name]
            if platform.system() == "Windows":
                args = args[1:]

            threading.Thread(
                target=subprocess.call,
                args=(args,),
            ).start()

        self._update_status("SPC played")

    ###########################################################################

    def on_porter_name_changed(self, val: str) -> None:
        self._update_state(porter=val)
        self._update_status(f"Porter name set to {val}")

    ###########################################################################

    def on_recent_projects_cleared(self) -> None:
        self.recent_projects = []
        self._update_status("Recent projects cleared")

    ###########################################################################

    def on_redo_clicked(self) -> None:
        if self._undo_level > 0:
            self._undo_level -= 1
            self._signal_state_change()
            self._update_status("Redo")

    ###########################################################################

    def on_reload_musicxml_clicked(self) -> None:
        self.song = Song.from_music_xml(self.state.musicxml_fname)

        instruments = {inst.name: inst for inst in self.state.instruments}

        for n, instrument in enumerate(self.song.instruments):
            if instrument.name in instruments:
                self.song.instruments[n] = instruments[instrument.name]

        self.state.instruments[:] = self.song.instruments
        self.reinforce_state()
        self._update_status("MusicXML reloaded")

    ###########################################################################

    def on_save(self) -> None:
        self._save_backup()

        path = self._project_path
        project = self.state.project_name

        if path is not None and project is not None:
            fname = path / (project + ".prj")
            save(fname, self.state)
            self.reinforce_state()
            self._update_status("Project saved")

    ###########################################################################

    def on_select_adsr_mode_selected(self, state: bool) -> None:
        self._update_inst_state(adsr_mode=state)
        self._update_status(
            f"Envelope mode set to {'ADSR' if state else 'Gain'}"
        )

    ###########################################################################

    def on_solo_changed(self, idx: int, state: bool) -> None:
        self._update_inst_state(idx=idx, solo=state)
        inst = self.state.instruments[idx].name
        self._update_status(f"{inst} solo {_endis(state)}")

    ###########################################################################

    def on_solo_percussion_changed(self, state: bool) -> None:
        self._update_state(solo_percussion=state)
        self._update_status(f"Percussion solo {_endis(state)}")

    ###########################################################################

    def on_start_measure_changed(self, value: int) -> None:
        self._update_state(start_measure=value)
        self._update_status(f"Start measure set to {value}")

    ###########################################################################

    def on_subtune_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_inst_state(subtune_setting=setting)
        self._update_status(f"Subtune set to {setting}")

    ###########################################################################

    def on_superloop_analysis_changed(self, enabled: bool) -> None:
        self._update_state(superloop_analysis=enabled)
        self._update_status(f"Superloop analysis {_endis(enabled)}")

    ###########################################################################

    def on_sus_level_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 7)
        self._update_inst_state(sus_level_setting=setting)
        self._update_status(f"Sustain level set to {setting}")

    ###########################################################################

    def on_sus_rate_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 31)
        self._update_inst_state(sus_rate_setting=setting)
        self._update_status(f"Decay rate set to {setting}")

    ###########################################################################

    def on_tune_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_inst_state(tune_setting=setting)
        self._update_status(f"Tune set to {setting}")

    ###########################################################################

    def on_undo_clicked(self) -> None:
        if self._undo_level < len(self._history) - 1:
            self._undo_level += 1
            self._signal_state_change()
            self._update_status("Undo")

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _append_recent_project(self, fname: Path) -> None:
        history = self.recent_projects
        if fname in history:
            history.remove(fname)
        history.append(fname)
        self.recent_projects = history

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
        if self.prefs_fname.exists():
            with open(self.prefs_fname, "r", encoding="utf8") as fobj:
                prefs = yaml.safe_load(fobj)

            self.preferences.amk_fname = Path(prefs["amk"]["path"])
            self.preferences.spcplay_fname = Path(prefs["spcplay"]["path"])
            self.preferences.sample_pack_dname = Path(
                prefs["sample_packs"]["path"]
            )
            self.preferences.advanced_mode = prefs.get("advanced", False)
            self._load_sample_packs()

        self.preferences_changed.emit(
            self.preferences.advanced_mode,
            bool(self.preferences.amk_fname.name),
            bool(self.preferences.spcplay_fname.name),
            self._sample_packs,
        )

    ###########################################################################

    def _load_sample_packs(self) -> None:

        self._sample_packs = {}

        packs = {}
        root_dir = self.preferences.sample_pack_dname
        for fname in glob("*.zip", root_dir=root_dir):
            pack = Path(fname)
            packs[pack.stem] = root_dir / pack

        for name, path in packs.items():
            try:
                self._sample_packs[name] = SamplePack(path)

            except FileNotFoundError:
                self.response_generated.emit(
                    True,
                    "Error loading sample pack",
                    f"Could not open sample pack {name} at {path}",
                )

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

    def _save_backup(self) -> None:
        path = self._project_path
        project = self.state.project_name

        if path is not None and project is not None:
            fname = path / (project + ".prj.bak")
            save(fname, self.state)

    ###########################################################################

    def _signal_state_change(
        self, update_instruments: bool = False, state_change: bool = True
    ) -> None:
        self.state.unsaved = state_change
        self.state_changed.emit(self.state, update_instruments)

    ###########################################################################

    def _update_echo_state(
        self,
        **kwargs: set[EchoCh]
        | tuple[float, float]
        | tuple[bool, bool]
        | int
        | float
        | bool,
    ) -> None:
        new_echo = replace(self.state.echo, **kwargs)
        self._update_state(echo=new_echo)

    ###########################################################################

    def _update_inst_state(
        self,
        idx: int = -1,
        **kwargs: str
        | int
        | dict[Dynamics, int]
        | dict[Artic, ArticSetting]
        | set[Dynamics]
        | bool
        | SampleSource
        | tuple[str, Path]
        | tuple[bool, bool]
        | Path
        | GainMode,
    ) -> None:
        old_inst = (
            self.state.inst if idx == -1 else self.state.instruments[idx]
        )
        try:
            new_inst = replace(old_inst, **kwargs)
        except TypeError:
            new_inst = replace(old_inst)
            for key, val in kwargs.items():
                setattr(new_inst, key, val)

        if new_inst != self.state.inst:
            self._rollback_undo()

            new_state = deepcopy(self.state)
            if idx == -1:
                new_state.inst = new_inst
            else:
                new_state.instruments[idx] = new_inst

            self._history.append(new_state)
            self._signal_state_change()

    ###########################################################################

    def _update_state(
        self,
        update_instruments: bool = False,
        **kwargs: str
        | bool
        | InstrumentConfig
        | list[InstrumentConfig]
        | None
        | EchoConfig
        | int,
    ) -> None:
        new_state = replace(self.state, **kwargs)
        if new_state != self.state:
            self._rollback_undo()

            self._save_backup()
            self._history.append(new_state)
            self._signal_state_change(update_instruments)

    ###########################################################################

    def _update_status(self, msg: str) -> None:
        self.status_updated.emit(msg)

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def config_dir(self) -> Path:
        app = "xml2mml"

        sys = platform.system()
        match sys:
            case "Linux":
                default = Path(os.environ["HOME"]) / ".config"
                conf_dir = Path(os.environ.get("XDG_CONFIG_HOME", default))
            case "Windows":
                conf_dir = Path(os.environ["APPDATA"])
            case "Darwin":
                conf_dir = Path(os.environ["HOME"]) / "Library"
            case _:
                raise SmwMusicException(f"Unknown OS {sys}")

        return conf_dir / app

    ###########################################################################

    @property
    def convert(self) -> list[str]:
        # TODO: Put better protections in place for this
        assert self._project_path is not None  # nosec: B101

        match platform.system():
            case "Darwin" | "Linux":
                return ["sh", "convert.sh"]
            case "Windows":
                return [str(self._project_path / "convert.bat")]
            case _:
                return []

    ###########################################################################

    @property
    def prefs_fname(self) -> Path:
        return self.config_dir / "preferences.yaml"

    ###########################################################################

    @property
    def recent_projects(self) -> list[Path]:
        fname = self.recent_projects_fname
        projects = None
        with suppress(FileNotFoundError):
            with open(fname, "r", encoding="utf8") as fobj:
                projects = yaml.safe_load(fobj)

        if projects is None:
            projects = []

        return [Path(project) for project in projects]

    ###########################################################################

    @recent_projects.setter
    def recent_projects(self, projects: list[Path]) -> None:
        project_limit = 5
        projects = projects[-project_limit:]

        with open(self.recent_projects_fname, "w", encoding="utf8") as fobj:
            yaml.safe_dump([str(project) for project in projects], fobj)

        self.recent_projects_updated.emit(projects)

    ###########################################################################

    @property
    def recent_projects_fname(self) -> Path:
        return self.config_dir / "projects.yaml"

    ###########################################################################

    @property
    def state(self) -> State:
        return self._history[-1 - self._undo_level]
