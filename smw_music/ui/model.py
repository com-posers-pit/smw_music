# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Music XML -> AMK Converter."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import hashlib
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
from music21.pitch import Pitch, PitchException
from PyQt6.QtCore import QObject, pyqtSignal
from watchdog import events, observers

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
    InstrumentSample,
    NoteHead,
    SampleSource,
)
from smw_music.music_xml.song import Song
from smw_music.ui.quotes import ashtley, quotes
from smw_music.ui.sample import SamplePack
from smw_music.ui.save import load, save
from smw_music.ui.state import NoSample, PreferencesState, State
from smw_music.ui.utilization import (
    Utilization,
    decode_utilization,
    echo_bytes,
)
from smw_music.ui.utils import make_vis_dir
from smw_music.utils import brr_size_b, newest_release

###############################################################################
# Private constant definitions
###############################################################################

_CURRENT_PREFS_VERSION = 0

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
# Private Class Definitions
###############################################################################


class _SamplePackWatcher(events.FileSystemEventHandler):
    def __init__(self, model: "Model") -> None:
        super().__init__()
        self._model = model

    ###########################################################################

    def on_created(
        self, event: events.FileCreatedEvent | events.DirCreatedEvent
    ) -> None:
        fname = Path(event.src_path).name
        self._model.update_status(f"Sample pack {fname} added")
        self._model.update_sample_packs()

    ###########################################################################

    def on_deleted(
        self, event: events.FileDeletedEvent | events.DirDeletedEvent
    ) -> None:
        fname = Path(event.src_path).name
        self._model.update_status(f"Sample pack {fname} removed")
        self._model.update_sample_packs()


###############################################################################
# API Class Definitions
###############################################################################


class Model(QObject):  # pylint: disable=too-many-public-methods
    state_changed = pyqtSignal(
        State, bool
    )  # arguments=['state', 'update_instruments']
    preferences_changed = pyqtSignal(
        bool, bool, bool, bool, bool
    )  # arguments = ['advanced_enabled', 'amk_valid', 'spcplayer_valid', 'dark_mode', 'confirm_render']
    instruments_changed = pyqtSignal(list)
    recent_projects_updated = pyqtSignal(list)
    sample_packs_changed = pyqtSignal(dict)

    mml_generated = pyqtSignal(str)  # arguments=['mml']
    status_updated = pyqtSignal(str)  # arguments=['message']
    response_generated = pyqtSignal(
        bool, str, str
    )  # arguments=["error", "title", "response"]
    utilization_updated = pyqtSignal(Utilization)

    song: Song | None
    preferences: PreferencesState
    _history: list[State]
    _undo_level: int
    _sample_packs: dict[str, SamplePack]
    _project_path: Path | None
    _sample_watcher: observers.Observer

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
        self._start_watcher()

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
            "stats",
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

        # Add visualizations directory
        make_vis_dir(path)

        # Apply updates to stock AMK files
        # https://www.smwcentral.net/?p=viewthread&t=98793&page=2&pid=1601787#p1601787
        fname = path / "music/originals/09 Bonus End.txt"
        with open(fname, "rb") as fobj:
            data = fobj.read()
        if hashlib.md5(data).hexdigest() == "7e9d4bd864cfc1e82272fb0a9379e318":
            contents = data.split(b"\n")
            contents = contents[:15] + contents[16:]
            data = b"\n".join(contents)
            with open(fname, "wb") as fobj:
                fobj.write(data)

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

        self._update_state()
        self._update_state(
            project_name=project_name,
            mml_fname=self._project_path / "music" / f"{project_name}.txt",
        )

        # TODO: Unify this project path with what's used in on_save
        self._append_recent_project(path / (project_name + ".prj"))
        self.update_status(f"Created project {project_name}")
        self.on_save()

    ###########################################################################

    def close_project(self) -> None:
        self._project_path = None
        self._update_state(update_instruments=True)
        self.update_status("Project closed")

    ###########################################################################

    def reinforce_state(self) -> None:
        self._signal_state_change(update_instruments=True, state_change=False)

    ###########################################################################

    def start(self) -> None:
        self._load_prefs()
        if self.preferences.release_check:
            release = newest_release()
            if release is not None and release[1] != __version__:
                url, version = release
                self.response_generated.emit(
                    False,
                    "New Version",
                    f"beer <a href={url}>v{version}</a> is available "
                    + "for download<br />Version checking can be disabled "
                    + "in preferences",
                )

        self.update_sample_packs()

        self.recent_projects_updated.emit(self.recent_projects)
        self.reinforce_state()

        quote: tuple[str, str] = choice(quotes)  # nosec: B311
        self.update_status(f"{quote[1]}: {quote[0]}")

    ###########################################################################

    def update_preferences(self, preferences: PreferencesState) -> None:
        prefs_dict = {
            "beer": __version__,
            "amk": {"path": str(preferences.amk_fname)},
            "spcplay": {"path": str(preferences.spcplay_fname)},
            "sample_packs": {"path": str(preferences.sample_pack_dname)},
            "advanced": preferences.advanced_mode,
            "dark_mode": preferences.dark_mode,
            "release_check": preferences.release_check,
            "confirm_render": preferences.confirm_render,
            "version": _CURRENT_PREFS_VERSION,
        }

        with open(self.prefs_fname, "w", encoding="utf8") as fobj:
            yaml.safe_dump(prefs_dict, fobj)

        self._load_prefs()

    ###########################################################################

    def update_sample_packs(self) -> None:
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

        self.sample_packs_changed.emit(self._sample_packs)

    ###########################################################################

    def update_status(self, msg: str) -> None:
        self.status_updated.emit(msg)

    ###########################################################################
    # API slot definitions
    ###########################################################################

    def on_artic_length_changed(self, artic: Artic, val: int | str) -> None:
        max_len = 7
        with suppress(NoSample):
            artics = deepcopy(self.state.sample.artics)
            artics[artic].length = _parse_setting(val, max_len)
            self._update_sample_state(artics=artics)
            self.update_status(f"{artic} length set to {val}")

    ###########################################################################

    def on_artic_volume_changed(self, artic: Artic, val: int | str) -> None:
        max_vol = 15
        with suppress(NoSample):
            artics = deepcopy(self.state.sample.artics)
            artics[artic].volume = _parse_setting(val, max_vol)
            self._update_sample_state(artics=artics)
            self.update_status(f"{artic} volume set to {val}")

    ###########################################################################

    def on_attack_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 15)
        self._update_sample_state(attack_setting=setting, adsr_mode=True)
        self.update_status(f"Attack set to {setting}")

    ###########################################################################

    def on_brr_fname_changed(self, fname: str) -> None:
        self._update_sample_state(
            brr_fname=Path(fname), sample_source=SampleSource.BRR
        )
        self.update_status(f"BRR set to {fname}")

    ###########################################################################

    def on_brr_sample_selected(self, state: bool) -> None:
        if state:
            self._update_sample_state(sample_source=SampleSource.BRR)
            self.update_status("Sample source set to BRR")

    ###########################################################################

    def on_brr_setting_changed(self, val: str) -> None:
        self._update_sample_state(brr_setting=val)
        self.update_status(f"BRR setting changed to {val}")

    ###########################################################################

    def on_builtin_sample_changed(self, index: int) -> None:
        self._update_sample_state(
            builtin_sample_index=index, sample_source=SampleSource.BUILTIN
        )
        self.update_status(f"Builtin sample {index} selected")

    ###########################################################################

    def on_builtin_sample_selected(self, state: bool) -> None:
        if state:
            self._update_sample_state(sample_source=SampleSource.BUILTIN)
            self.update_status("Sample source set to builtin")

    ###########################################################################

    def on_decay_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 7)
        self._update_sample_state(decay_setting=setting, adsr_mode=True)
        self.update_status(f"Decay set to {setting}")

    ###########################################################################

    def on_dynamics_changed(self, level: Dynamics, val: int | str) -> None:
        setting = _parse_setting(val)
        state = self.state
        with suppress(NoSample):
            if state.sample.dyn_interpolate:
                self._interpolate(level, setting)
            else:
                dynamics = deepcopy(state.sample.dynamics)
                dynamics[level] = setting
                self._update_sample_state(dynamics=dynamics)
            self.update_status(f"Dynamics {level} set to {setting}")

    ###########################################################################

    def on_echo_en_changed(self, chan: EchoCh, state: bool) -> None:
        enables = deepcopy(self.state.echo.enables)
        if state:
            enables.add(chan)
        else:
            enables.remove(chan)
        self._update_echo_state(enables=enables)
        self.update_status(f"Echo {str(chan)} {_endis(state)}")

    ###########################################################################

    def on_echo_feedback_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 128) / 128
        self._update_echo_state(fb_mag=setting)
        self.update_status(f"Echo feedback magnitude set to {setting}")

    ###########################################################################

    def on_echo_feedback_surround_changed(self, state: bool) -> None:
        self._update_echo_state(fb_inv=state)
        self.update_status(f"Echo feedback surround {_endis(state)}")

    ###########################################################################

    def on_echo_left_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 128) / 128
        self._update_echo_state(vol_mag=(setting, self.state.echo.vol_mag[1]))
        self.update_status(f"Echo left channel magnitude set to {setting}")

    ###########################################################################

    def on_echo_left_surround_changed(self, state: bool) -> None:
        self._update_echo_state(vol_inv=(state, self.state.echo.vol_inv[1]))
        self.update_status(f"Echo left channel surround {_endis(state)}")

    ###########################################################################

    def on_echo_right_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 128) / 128
        self._update_echo_state(vol_mag=(self.state.echo.vol_mag[0], setting))
        self.update_status(f"Echo right channel magnitude set to {setting}")

    ###########################################################################

    def on_echo_right_surround_changed(self, state: bool) -> None:
        self._update_echo_state(vol_inv=(self.state.echo.vol_inv[0], state))
        self.update_status(f"Echo right channel surround {_endis(state)}")

    ###########################################################################

    def on_echo_delay_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 15)
        self._update_echo_state(delay=setting)
        self.update_status(f"Echo delay changed to {val}")

    ###########################################################################

    def on_filter_0_toggled(self, state: bool) -> None:
        self._update_echo_state(fir_filt=0 if state else 1)
        self.update_status(f"Echo filter set to {0 if state else 1}")

    ###########################################################################

    def on_gain_declin_selected(self, state: bool) -> None:
        self._select_gain(state, GainMode.DECLIN, "Decreasing linear")

    ###########################################################################

    def on_gain_decexp_selected(self, state: bool) -> None:
        self._select_gain(state, GainMode.DECEXP, "Decreasing exponential")

    ###########################################################################

    def on_gain_direct_selected(self, state: bool) -> None:
        if state:
            self._update_sample_state(
                gain_mode=GainMode.DIRECT, adsr_mode=False
            )
            self.update_status("Direct gain envelope selected")

    ###########################################################################

    def on_gain_incbent_selected(self, state: bool) -> None:
        self._select_gain(state, GainMode.INCBENT, "Increasing bent")

    ###########################################################################

    def on_gain_inclin_selected(self, state: bool) -> None:
        self._select_gain(state, GainMode.INCLIN, "Increasing linear")

    ###########################################################################

    def on_gain_changed(self, val: int | str) -> None:
        with suppress(NoSample):
            mode = self.state.sample.gain_mode
            # TODO: Unify this 31 with the others
            limit = 127 if mode == GainMode.DIRECT else 31
            setting = _parse_setting(val, limit)
            self._update_sample_state(gain_setting=setting, adsr_mode=False)
            self.update_status("Gain setting changed to {setting}")

    ###########################################################################

    def on_game_name_changed(self, val: str) -> None:
        self._update_state(game=val)
        self.update_status(f"Game name set to {val}")

    ###########################################################################

    def on_generate_and_play_clicked(self) -> None:
        self.update_status("SPC generated and played")
        if self._on_generate_mml_clicked(False):
            if self._on_generate_spc_clicked(False):
                self.on_play_spc_clicked()

    ###########################################################################

    def on_generate_mml_clicked(self, report: bool = True) -> None:
        self._on_generate_mml_clicked(report)

    ###########################################################################

    def on_generate_spc_clicked(self, report: bool = True) -> None:
        self._on_generate_spc_clicked(report)

    ###########################################################################

    def on_global_echo_en_changed(self, state: bool) -> None:
        self._update_state(global_echo_enable=state)
        self.update_status(f"Echo {_endis(state)}")

    ###########################################################################

    def on_global_legato_changed(self, state: bool) -> None:
        self._update_state(global_legato=state)
        self.update_status(f"Global legato {_endis(state)}")

    ###########################################################################

    def on_global_volume_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_state(global_volume=setting)
        self.update_status(f"Global volume set to {setting}")

    ###########################################################################

    def on_interpolate_changed(self, state: bool) -> None:
        with suppress(NoSample):
            sample_idx = self.state.sample_idx
            sample_name = sample_idx[1] or sample_idx[0]

            self._update_sample_state(dyn_interpolate=state)
            self.update_status(
                f"Dynamics interpolation for {sample_name} {_endis(state)}"
            )

    ###########################################################################

    def on_load(self, fname: Path) -> None:
        try:
            save_state, backup_fname = load(fname)
            if backup_fname is not None:
                self.response_generated.emit(
                    False,
                    "Old File",
                    "This project uses an old save file format.  "
                    "We've tried our best to upgrade, but there might still "
                    "be some problems.  Your old save file was backed up as "
                    f"{backup_fname}, you should probably keep a copy until "
                    "you've confirmed the upgrade was successful.  Or fixed "
                    "any problems with it, it's all the same to beer.",
                )

        except SmwMusicException as e:
            self.response_generated.emit(True, "Invalid save version", str(e))
        except FileNotFoundError:
            self.response_generated.emit(
                True, "Invalid project file", "Could not find project file"
            )
        else:
            self._append_recent_project(fname)

            self._undo_level = 0
            self._history = [replace(save_state)]
            self._project_path = fname.parent
            musicxml = self.state.musicxml_fname
            if musicxml is None:
                self.song = None
            else:
                self._load_musicxml(musicxml, True)

            self.reinforce_state()
            self.update_status(f"Opened project {self.state.project_name}")

    ###########################################################################

    def on_loop_analysis_changed(self, enabled: bool) -> None:
        self._update_state(loop_analysis=enabled)
        self.update_status(f"Loop analysis {_endis(enabled)}")

    ###########################################################################

    def on_measure_numbers_changed(self, enabled: bool) -> None:
        self._update_state(measure_numbers=enabled)
        self.update_status(f"Measure # reporting {_endis(enabled)}")

    ###########################################################################

    def on_mml_fname_changed(self, fname: str) -> None:
        self._update_state(mml_fname=fname)
        self.update_status(f"MML name set to {fname}")

    ###########################################################################

    def on_multisample_sample_add_clicked(
        self, name: str, notes: str, notehead: str, output: str
    ) -> None:
        self._multisample_changed(True, name, notes, notehead, output)

    ###########################################################################

    def on_multisample_sample_changed(
        self, name: str, notes: str, notehead: str, output: str
    ) -> None:
        self._multisample_changed(False, name, notes, notehead, output)

    ###########################################################################

    def on_multisample_sample_remove_clicked(self) -> None:
        state = self.state
        with suppress(NoSample):
            inst, sample = state.sample_idx
            if sample:
                instruments = deepcopy(state.instruments)
                keys = sorted(instruments[inst].multisamples.keys())
                instruments[inst].multisamples.pop(sample)

                idx = keys.index(sample)
                try:
                    new_inst = keys[idx + 1]
                except IndexError:
                    new_inst = keys[idx - 1] if idx else ""

                self._update_state(
                    update_instruments=True,
                    instruments=instruments,
                    sample_idx=(inst, new_inst),
                )
                self.update_status(
                    f"Removed sample {sample} from instrument {inst}"
                )

    ###########################################################################

    def on_multisample_sample_selected(self, state: bool) -> None:
        return
        # if state:
        #     self._update_sample_state(sample_source=SampleSource.MULTISAMPLE)
        #     self.update_status("Sample source set to multisample")

    ###########################################################################

    def on_musicxml_fname_changed(self, fname: str) -> None:
        file_path = Path(fname)
        if file_path == self.state.musicxml_fname:
            return

        self._load_musicxml(file_path, False)

        self._update_state(True, musicxml_fname=file_path)
        self.update_status(f"MusicXML name set to {fname}")

    ###########################################################################

    def on_octave_shift_changed(self, octave_shift: int) -> None:
        self._update_sample_state(octave_shift=octave_shift)
        self.update_status(f"Octave set to {octave_shift}")

    ###########################################################################

    def on_pack_sample_changed(self, item_id: tuple[str, Path]) -> None:
        self._update_sample_state(
            pack_sample=item_id, sample_source=SampleSource.SAMPLEPACK
        )
        self._load_sample_settings(item_id)
        self.update_status(
            f"Sample pack {item_id[0]}:{str(item_id[1])} selected"
        )

    ###########################################################################

    def on_pack_sample_selected(self, state: bool) -> None:
        with suppress(NoSample):
            if state:
                self._update_sample_state(
                    sample_source=SampleSource.SAMPLEPACK
                )
                self.update_status("Sample source set to sample pack")
                sample = self.state.sample.pack_sample
                if sample[0]:
                    self._load_sample_settings(sample)

    ###########################################################################

    def on_pan_enable_changed(self, state: bool) -> None:
        self._update_sample_state(pan_enabled=state)
        self.update_status(f"Pan {_endis(state)}")

    ###########################################################################

    def on_pan_invert_changed(self, left: bool, state: bool) -> None:
        with suppress(NoSample):
            pan_setting = list(self.state.sample.pan_invert)
            pan_setting[0 if left else 1] = state

            self._update_sample_state(
                pan_invert=(pan_setting[0], pan_setting[1])
            )
            self.update_status(
                f'Pan {"left" if left else "right"} inversion {_endis(state)}'
            )

    ###########################################################################

    def on_pan_setting_changed(self, val: int) -> None:
        self._update_sample_state(pan_setting=val)
        self.update_status(f"Pan changed to {val}")

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

        self.update_status("SPC played")

    ###########################################################################

    def on_porter_name_changed(self, val: str) -> None:
        self._update_state(porter=val)
        self.update_status(f"Porter name set to {val}")

    ###########################################################################

    def on_recent_projects_cleared(self) -> None:
        self.recent_projects = []
        self.update_status("Recent projects cleared")

    ###########################################################################

    def on_redo_clicked(self) -> None:
        if self._undo_level > 0:
            self._undo_level -= 1
            self._signal_state_change(update_aram_util=False)
            self.update_status("Redo")

    ###########################################################################

    def on_reload_musicxml_clicked(self) -> None:
        assert self.state.musicxml_fname is not None
        self._load_musicxml(self.state.musicxml_fname, True)

        self.reinforce_state()
        self.update_status("MusicXML reloaded")

    ###########################################################################

    def on_render_zip_clicked(self) -> None:
        self.update_status("Zip file generated")

        path = self._project_path
        project = self.state.project_name

        assert path is not None  # nosec: B101
        assert project is not None  # nosec: B101

        # Turn off the preview features
        self.state.start_measure = 1
        for sample in self.state.samples.values():
            sample.mute = False
            sample.solo = False
        self.reinforce_state()

        self.on_generate_mml_clicked(False)
        self.on_generate_spc_clicked(False)

        proj = Path(project)
        mml_fname = path / "music" / proj.with_suffix(".txt")
        spc_fname = path / "SPCs" / proj.with_suffix(".spc")
        sample_path = path / "samples" / project

        zname = str(path / (project + ".zip"))
        with zipfile.ZipFile(zname, "w") as zobj:
            zobj.write(mml_fname, mml_fname.name)
            zobj.write(spc_fname, spc_fname.name)
            for brr in glob("**/*.brr", root_dir=sample_path, recursive=True):
                zobj.write(sample_path / brr, arcname=str(proj / brr))

        self.response_generated.emit(
            False, "Zip Render", f"Zip file {zname} rendered"
        )

    ###########################################################################

    def on_sample_changed(self, sample_idx: tuple[str, str]) -> None:
        self._update_state(sample_idx=sample_idx)

        inst, sample = sample_idx
        name = sample or inst
        self.update_status(f"{name} selected")

    ###########################################################################

    def on_save(self) -> None:
        self._save_backup()

        path = self._project_path
        project = self.state.project_name

        if path is not None and project is not None:
            fname = path / (project + ".prj")
            save(fname, self.state)
            self.reinforce_state()
            self.update_status("Project saved")

    ###########################################################################

    def on_select_adsr_mode_selected(self, state: bool) -> None:
        self._update_sample_state(adsr_mode=state)
        self.update_status(
            f"Envelope mode set to {'ADSR' if state else 'Gain'}"
        )

    ###########################################################################

    def on_solomute_changed(
        self, sample_idx: tuple[str, str], solo: bool, state: bool
    ) -> None:
        inst_name, sample_name = sample_idx
        instruments = deepcopy(self.state.instruments)
        inst = instruments[inst_name]

        field = "solo" if solo else "mute"
        update = {field: state}

        if sample_name:
            msg = f"{inst_name}.{sample_name}"
            inst.multisamples[sample_name] = replace(
                inst.multisamples[sample_name], **update
            )
            # If a sample's solo/mute is being disabled, disable it in the
            # instrument as well
            if not state:
                inst.sample = replace(inst.sample, **update)

        else:
            # Apply an instrument mute/solo to all samples
            msg = f"{inst_name}"
            inst.sample = replace(inst.sample, **update)
            for sample_name, sample in inst.multisamples.items():
                inst.multisamples[sample_name] = replace(sample, **update)

        self._update_state(instruments=instruments)

        self.update_status(f"{msg} {field} {_endis(state)}")

    ###########################################################################

    def on_start_measure_changed(self, value: int) -> None:
        self._update_state(start_measure=value)
        self.update_status(f"Start measure set to {value}")

    ###########################################################################

    def on_subtune_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_sample_state(subtune_setting=setting)
        self.update_status(f"Subtune set to {setting}")

    ###########################################################################

    def on_superloop_analysis_changed(self, enabled: bool) -> None:
        self._update_state(superloop_analysis=enabled)
        self.update_status(f"Superloop analysis {_endis(enabled)}")

    ###########################################################################

    def on_sus_level_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 7)
        self._update_sample_state(sus_level_setting=setting, adsr_mode=True)
        self.update_status(f"Sustain level set to {setting}")

    ###########################################################################

    def on_sus_rate_changed(self, val: int | str) -> None:
        setting = _parse_setting(val, 31)
        self._update_sample_state(sus_rate_setting=setting, adsr_mode=True)
        self.update_status(f"Decay rate set to {setting}")

    ###########################################################################

    def on_tune_changed(self, val: int | str) -> None:
        setting = _parse_setting(val)
        self._update_sample_state(tune_setting=setting)
        self.update_status(f"Tune set to {setting}")

    ###########################################################################

    def on_undo_clicked(self) -> None:
        if self._undo_level < len(self._history) - 1:
            self._undo_level += 1
            self._signal_state_change(update_aram_util=False)
            self.update_status("Undo")

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
        inst = self.state.instrument
        sample = self.state.sample
        dyns = sorted(inst.dynamics_present)
        dynamics = deepcopy(sample.dynamics)

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

        self._update_sample_state(force_update=True, dynamics=dynamics)

    ###########################################################################

    def _load_musicxml(self, musicxml: Path, keep_inst_settings: bool) -> None:
        try:
            self.song = Song.from_music_xml(str(musicxml))
        except MusicXmlException as e:
            self.response_generated.emit(
                True,
                "Error loading score",
                f"Could not open score {musicxml}: {str(e)}",
            )
        else:
            if keep_inst_settings:
                # Reconcile instrument settings
                for inst_name, song_inst in self.song.instruments.items():
                    with suppress(KeyError):
                        state_inst = self.state.instruments[inst_name]
                        song_inst.solo = state_inst.solo
                        song_inst.mute = state_inst.mute
                        song_inst.samples = state_inst.samples

            self.state.instruments = deepcopy(self.song.instruments)

            if self._on_generate_mml_clicked(False):
                self._on_generate_spc_clicked(False)

    ###########################################################################

    def _load_prefs(self) -> None:
        if self.prefs_fname.exists():
            with open(self.prefs_fname, "r", encoding="utf8") as fobj:
                prefs = yaml.safe_load(fobj)

            prefs_version = prefs.get("version", _CURRENT_PREFS_VERSION)

            if prefs_version > _CURRENT_PREFS_VERSION:
                raise SmwMusicException(
                    f"Preferences file version is {prefs_version}, tool "
                    + f"version only supports up to {_CURRENT_PREFS_VERSION}"
                )

            self.preferences = PreferencesState()
            self.preferences.amk_fname = Path(prefs["amk"]["path"])
            self.preferences.spcplay_fname = Path(prefs["spcplay"]["path"])
            self.preferences.sample_pack_dname = Path(
                prefs["sample_packs"]["path"]
            )
            with suppress(KeyError):
                self.preferences.advanced_mode = prefs["advanced"]
            with suppress(KeyError):
                self.preferences.dark_mode = prefs["dark_mode"]
            with suppress(KeyError):
                self.preferences.release_check = prefs["release_check"]
            with suppress(KeyError):
                self.preferences.confirm_render = prefs["confirm_render"]

        self._start_watcher()

        self.preferences_changed.emit(
            self.preferences.advanced_mode,
            bool(self.preferences.amk_fname.name),
            bool(self.preferences.spcplay_fname.name),
            self.preferences.dark_mode,
            self.preferences.confirm_render,
        )
        self.reinforce_state()

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
        self._update_sample_state(**new_state)

    ###########################################################################

    def _multisample_changed(
        self, new: bool, name: str, notes: str, notehead: str, output: str
    ) -> None:
        state = self.state

        # All the inputs need to be present to continue
        if not all([name, notes, notehead, output]):
            return

        # Make sure we've got an instrument selected
        try:
            sample = state.sample
        except NoSample:
            return

        # Exit if we're trying to change a sample that doesn't exist (this can
        # happen when tabbing through and entering values before adding it
        if not new and name not in state.instrument.multisamples:
            return

        # Parse the input parameters and bail if something went wrong
        try:
            if ":" in notes:
                llim = Pitch(notes.split(":")[0])
                ulim = Pitch(notes.split(":")[1])
            else:
                llim = ulim = Pitch(notes)

            head = NoteHead.from_symbol(notehead)
            start = Pitch(output)
        except (PitchException, ValueError) as e:
            self.response_generated.emit(True, "Multisample error", str(e))
            return

        if new:
            sample = InstrumentSample(
                ulim=ulim, llim=llim, notehead=head, start=start
            )
        else:
            sample = replace(
                sample,
                llim=llim,
                ulim=ulim,
                start=start,
                notehead=head,
            )

        inst, _ = state.sample_idx

        instruments = deepcopy(state.instruments)
        instruments[inst].multisamples[name] = sample
        self._update_state(
            update_instruments=True,
            instruments=instruments,
            sample_idx=(inst, name),
        )
        if new:
            msg = f"Added multisample {name} to {inst}"
        else:
            msg = f"Updated multisample {name} of {inst}"

        self.update_status(msg)

    ###########################################################################

    def _on_generate_mml_clicked(self, report: bool = True) -> bool:
        assert self.state.mml_fname is not None

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

                self.song.instruments = deepcopy(self.state.instruments)

                self.song.volume = self.state.global_volume
                if self.state.porter:
                    self.song.porter = self.state.porter
                if self.state.game:
                    self.song.game = self.state.game

                mml = self.song.to_mml_file(
                    str(fname),
                    self.state.global_legato,
                    self.state.loop_analysis,
                    self.state.superloop_analysis,
                    self.state.measure_numbers,
                    True,
                    self.state.echo if self.state.global_echo_enable else None,
                    PurePosixPath(self.state.project_name),
                    self.state.start_measure,
                )
                self.mml_generated.emit(mml)
                self.update_status("MML generated")
            except MusicXmlException as e:
                msg = str(e)
            else:
                error = False
                msg = "Done"

        if report or error:
            self.response_generated.emit(error, title, msg)

        return not error

    ###########################################################################

    def _on_generate_spc_clicked(self, report: bool = True) -> bool:
        assert self._project_path is not None  # nosec: B101
        assert self.state.project_name is not None  # nosec: B101
        assert self.state.mml_fname is not None

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
            os.makedirs(samples_path, exist_ok=True)

            for inst in self.state.instruments.values():
                for sample in inst.samples.values():
                    if sample.sample_source == SampleSource.BRR:
                        shutil.copy2(sample.brr_fname, samples_path)
                    if sample.sample_source == SampleSource.SAMPLEPACK:
                        pack_name, pack_path = sample.pack_sample
                        target = samples_path / pack_name / pack_path
                        os.makedirs(target.parents[0], exist_ok=True)
                        with open(target, "wb") as fobj:
                            try:
                                fobj.write(
                                    self._sample_packs[pack_name][
                                        pack_path
                                    ].data
                                )
                            except KeyError:
                                error = True
                                msg += (
                                    f"Could not find sample pack {pack_name}\n"
                                )

            if not error:
                try:
                    msg = subprocess.check_output(  # nosec B603
                        self.convert,
                        cwd=self._project_path,
                        stderr=subprocess.STDOUT,
                        timeout=15,
                    ).decode()
                except subprocess.CalledProcessError as e:
                    error = True
                    msg = e.output.decode("utf8")
                except subprocess.TimeoutExpired:
                    error = True
                    msg = "Conversion timed out"

        if report or error:
            self.response_generated.emit(error, "SPC Generated", msg)
            self.update_status("SPC generated")

        if not error:
            self._update_utilization_from_amk()
            self.reinforce_state()

        return not error

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

    def _select_gain(self, state: bool, mode: GainMode, caption: str) -> None:
        if state:
            kwargs: dict[str, GainMode | int | bool] = {
                "gain_mode": mode,
                "adsr_mode": False,
            }
            with suppress(NoSample):
                kwargs["gain_setting"] = min(
                    31, self.state.sample.gain_setting
                )

            self._update_sample_state(**kwargs)
            self.update_status(f"{caption} envelope selected")

    ###########################################################################

    def _signal_state_change(
        self,
        update_instruments: bool = False,
        state_change: bool = True,
        update_aram_util: bool = True,
    ) -> None:
        state = self.state

        state.unsaved = state_change
        self.state.unmapped = set()

        self._update_aram_util()

        with suppress(NoSample):
            if self.song:
                name = state.sample_idx[0]

                unmapped = self.song.unmapped_notes(
                    name, state.instruments[name]
                )

                self.state.unmapped = {
                    (pitch, str(head)) for pitch, head in unmapped
                }
        self.state_changed.emit(self.state, update_instruments)

    ###########################################################################

    def _start_watcher(self) -> None:
        with suppress(AttributeError):
            if self._sample_watcher.is_alive():
                self._sample_watcher.stop()
                self._sample_watcher.join()

        self._sample_watcher = observers.Observer()
        self._sample_watcher.daemon = True

        self._sample_watcher.schedule(
            _SamplePackWatcher(self), self.preferences.sample_pack_dname, False
        )
        self._sample_watcher.start()

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

    def _update_sample_state(
        self,
        force_update: bool = False,
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
        with suppress(NoSample):
            old_sample = self.state.sample
            new_sample = replace(old_sample)
            for key, val in kwargs.items():
                setattr(new_sample, key, val)

            if (new_sample != old_sample) or force_update:
                self._rollback_undo()

                new_state = deepcopy(self.state)
                new_state.sample = new_sample

                self._history.append(new_state)
                self._signal_state_change()

    ###########################################################################

    def _update_state(
        self,
        update_instruments: bool = False,
        **kwargs: str
        | bool
        | InstrumentConfig
        | dict[str, InstrumentConfig]
        | None
        | EchoConfig
        | int
        | tuple[str, str | None]
        | Path,
    ) -> None:
        if kwargs:
            new_state = replace(self.state)
            for key, val in kwargs.items():
                setattr(new_state, key, val)
        else:
            new_state = State()

        if new_state != self.state:
            self._rollback_undo()

            self._save_backup()
            self._history.append(new_state)
            self._signal_state_change(update_instruments)

    ###########################################################################

    def _update_aram_util(self) -> None:
        state = self.state
        aram_util = state.aram_util

        delay = state.echo.delay if state.global_echo_enable else 0
        aram_util.echo, aram_util.echo_pad = echo_bytes(delay)

        aram_util.samples += self.sample_bytes - state.aram_custom_sample_b

        state.aram_custom_sample_b = self.sample_bytes

    ###########################################################################

    def _update_utilization_from_amk(self) -> None:
        assert self._project_path is not None  # nosec: B101

        # TODO: Unify this with make_vis_dir
        png = (
            self._project_path
            / "Visualizations"
            / f"{self.state.project_name}.png"
        )

        self.state.aram_util = decode_utilization(png)
        self.state.aram_custom_sample_b = self.sample_bytes

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
    def sample_bytes(self) -> int:
        handled: list[tuple[bool, str, Path]] = []

        total_size = 0
        # TODO: Unify sample size calcs
        for sample in self.state.samples.values():
            size = 0
            if sample.sample_source == SampleSource.SAMPLEPACK:
                is_pack = True
                pack, path = sample.pack_sample
                if pack:
                    size = brr_size_b(len(self._sample_packs[pack][path].data))
            else:
                is_pack = False
                pack = ""
                path = sample.brr_fname
                with suppress(FileNotFoundError):
                    size = brr_size_b(os.stat(path).st_size)

            key = (is_pack, pack, path)
            if key not in handled:
                handled.append(key)
                total_size += size

        return total_size

    ###########################################################################

    @property
    def state(self) -> State:
        return self._history[-1 - self._undo_level]
