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
import threading
from contextlib import suppress
from copy import deepcopy
from dataclasses import replace
from glob import glob
from pathlib import Path
from random import choice
from typing import Callable

# Library imports
from music21.pitch import Pitch, PitchException
from PyQt6.QtCore import QObject, pyqtSignal
from watchdog import events, observers

# Package imports
import smw_music.spcmw as spcmw
from smw_music.common import SmwMusicException, __version__
from smw_music.exporters.mml import MmlExporter
from smw_music.ext_tools import spcplay
from smw_music.ext_tools.amk import BuiltinSampleGroup, BuiltinSampleSource
from smw_music.song import NoteHead, Song, SongException
from smw_music.spc700 import (
    SAMPLE_FREQ,
    Brr,
    EchoConfig,
    Envelope,
    GainMode,
    SamplePlayer,
    midi_to_nspc,
)
from smw_music.spcmw import (
    Artic,
    ArticSetting,
    Dynamics,
    InstrumentSample,
    Preferences,
    Project,
    ProjectInfo,
    ProjectSettings,
    SamplePack,
    SampleSource,
    TuneSource,
    Tuning,
    amk,
    extract_instruments,
    get_preferences,
)
from smw_music.utils import brr_size_b, newest_release, version_tuple

from .quotes import quotes
from .state import NoSample, State
from .utilization import echo_bytes
from .utils import endis, parse_setting

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


class NoSong(SmwMusicException):
    pass


###############################################################################


class Model(QObject):  # pylint: disable=too-many-public-methods
    state_changed = pyqtSignal()
    preferences_changed = pyqtSignal(
        (bool, bool, bool, bool, bool),
        arguments=[
            "advanced_enable",
            "amk_valid",
            "spcplayer_valid",
            "dark_mode",
            "confirm_render",
        ],  # type: ignore[call-arg]
    )
    instruments_changed = pyqtSignal(
        list, arguments=["instruments"]  # type: ignore[call-arg]
    )
    recent_projects_updated = pyqtSignal(
        list, arguments=["projects"]  # type: ignore[call-arg]
    )
    sample_packs_changed = pyqtSignal(
        dict, arguments=["sample_packs"]  # type:ignore[call-arg]
    )

    mml_generated = pyqtSignal(
        str, arguments=["mml"]  # type: ignore[call-arg]
    )
    status_updated = pyqtSignal(
        str, arguments=["message"]  # type: ignore[call-arg]
    )
    response_generated = pyqtSignal(
        (bool, str, str),
        arguments=["error", "title", "response"],  # type: ignore[call-arg]
    )
    songinfo_changed = pyqtSignal(
        str, arguments=["songinfo"]  # type: ignore[call-arg]
    )

    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self) -> None:
        super().__init__()
        self.preferences = get_preferences()
        self.saved = True
        self._history: list[State] = []
        self._undo_level = 0
        self._reset_state()
        self._reset_song()
        self._sample_packs: dict[str, SamplePack] = {}
        self._sample_player = SamplePlayer()

        self._start_watcher()

    ###########################################################################
    # API method definitions
    ###########################################################################

    def create_project(self, proj_dir: Path, info: ProjectInfo) -> None:
        project = spcmw.create_project(proj_dir, info)
        self._append_recent_project(project.project_fname)

        self._reset_state(project)

        self.update_status(f"Created project {project.info.project_name}")
        self.on_save()

    ###########################################################################

    def close_project(self) -> None:
        self._reset_state()
        self._signal_state_change()
        self.update_status("Project closed")

    ###########################################################################

    def reinforce_state(self) -> None:
        self._signal_state_change()

    ###########################################################################

    def start(self) -> None:
        self._check_first_use()
        self._load_prefs()
        self._check_for_updates()
        self.update_sample_packs()

        self.recent_projects_updated.emit(spcmw.get_recent_projects())

        self.reinforce_state()
        self._emit_quote()

    ###########################################################################

    def update_preferences(self, preferences: Preferences) -> None:
        spcmw.save_preferences(preferences)
        self._load_prefs()

    ###########################################################################

    def update_project_info(self, info: ProjectInfo) -> None:
        old_info = self.info
        self.info = info
        changed = []
        if old_info.project_name != info.project_name:
            changed.append(f"project name to {info.project_name}")
        if old_info.musicxml_fname != info.musicxml_fname:
            changed.append(f"MusicXML to {str(info.musicxml_fname)}")
            self._load_musicxml(self.project)
        if old_info.composer != info.composer:
            changed.append(f"composer to {info.composer}")
        if old_info.title != info.title:
            changed.append(f"title to {info.title}")
        if old_info.porter != info.porter:
            changed.append(f"porter to {info.porter}")
        if old_info.game != info.game:
            changed.append(f"game to {info.game}")

        if changed:
            self.update_status(f"Change {', '.join(changed)}")

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

    def on_apply_suggested_tune_clicked(self) -> None:
        setting = self.state.calculated_tune[1][0]
        tune, subtune = divmod(setting, 256)
        self._update_sample_state(tune_setting=tune, subtune_setting=subtune)
        self.update_status(f"Tune setting set to {tune}.{subtune}")

    ###########################################################################

    def on_artic_length_changed(self, artic: Artic, val: int | str) -> None:
        max_len = 7
        with suppress(NoSample):
            artics = deepcopy(self.state.sample.artics)
            artics[artic].length = parse_setting(val, max_len)
            self._update_sample_state(artics=artics)
            self.update_status(f"{artic} length set to {val}")

    ###########################################################################

    def on_artic_volume_changed(self, artic: Artic, val: int | str) -> None:
        max_vol = 15
        with suppress(NoSample):
            artics = deepcopy(self.state.sample.artics)
            artics[artic].volume = parse_setting(val, max_vol)
            self._update_sample_state(artics=artics)
            self.update_status(f"{artic} volume set to {val}")

    ###########################################################################

    def on_attack_changed(self, val: int | str) -> None:
        setting = parse_setting(val, 15)
        self._update_envelope_state(attack_setting=setting, adsr_mode=True)
        self.update_status(f"Attack set to {setting}")

    ###########################################################################

    def on_audition_start(self, audition_note: str) -> None:
        sample = self.state.sample
        tune = 256 * sample.tune_setting + sample.subtune_setting
        note = midi_to_nspc(Pitch(audition_note).midi)

        sample = self.state.sample
        play = False
        target: Callable[[bytes, Envelope, int, int, int], None] | Callable[
            [Path, Envelope, int, int, int], None
        ]
        arg: bytes | Path
        match sample.sample_source:
            case SampleSource.SAMPLEPACK:
                play = True
                pack, path = sample.pack_sample
                target = self._sample_player.play_bin
                arg = self._sample_packs[pack][path].data
            case SampleSource.BRR:
                play = True
                target = self._sample_player.play_file
                arg = sample.brr_fname

        if play:
            self._sample_player_th = threading.Thread(
                target=target, args=(arg, sample.envelope, tune, note, 0)
            )
            self._sample_player_th.start()

    ###########################################################################

    def on_audition_stop(self) -> None:
        self._sample_player.stop()

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
        setting = parse_setting(val, 7)
        self._update_envelope_state(decay_setting=setting, adsr_mode=True)
        self.update_status(f"Decay set to {setting}")

    ###########################################################################

    def on_dynamics_changed(self, level: Dynamics, val: int | str) -> None:
        setting = parse_setting(val)
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

    def on_echo_feedback_changed(self, val: int | str) -> None:
        setting = parse_setting(val, 128) / 128
        self.echo = replace(self.echo, fb_mag=setting)
        self.update_status(f"Echo feedback magnitude set to {setting}")

    ###########################################################################

    def on_echo_feedback_surround_changed(self, state: bool) -> None:
        self.echo = replace(self.echo, fb_inv=state)
        self.update_status(f"Echo feedback surround {endis(state)}")

    ###########################################################################

    def on_echo_left_changed(self, val: int | str) -> None:
        setting = parse_setting(val, 128) / 128
        self.echo = replace(self.echo, vol_mag=(setting, self.echo.vol_mag[1]))
        self.update_status(f"Echo left channel magnitude set to {setting}")

    ###########################################################################

    def on_echo_left_surround_changed(self, state: bool) -> None:
        self.echo = replace(self.echo, vol_inv=(state, self.echo.vol_inv[1]))
        self.update_status(f"Echo left channel surround {endis(state)}")

    ###########################################################################

    def on_echo_right_changed(self, val: int | str) -> None:
        setting = parse_setting(val, 128) / 128
        self.echo = replace(self.echo, vol_mag=(self.echo.vol_mag[0], setting))
        self.update_status(f"Echo right channel magnitude set to {setting}")

    ###########################################################################

    def on_echo_right_surround_changed(self, state: bool) -> None:
        self.echo = replace(self.echo, vol_inv=(self.echo.vol_inv[0], state))
        self.update_status(f"Echo right channel surround {endis(state)}")

    ###########################################################################

    def on_echo_delay_changed(self, val: int | str) -> None:
        setting = parse_setting(val, 15)
        self.echo = replace(self.echo, delay=setting)
        self.update_status(f"Echo delay changed to {val}")

    ###########################################################################

    def on_filter_0_toggled(self, state: bool) -> None:
        self.echo = replace(self.echo, fir_filt=0 if state else 1)
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
            self._update_envelope_state(
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
            mode = self.state.sample.envelope.gain_mode
            # TODO: Unify this 31 with the others
            limit = 127 if mode == GainMode.DIRECT else 31
            setting = parse_setting(val, limit)
            self._update_envelope_state(gain_setting=setting, adsr_mode=False)
            self.update_status("Gain setting changed to {setting}")

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
        self.settings = replace(self.settings, global_echo=state)
        self.update_status(f"Echo {endis(state)}")

    ###########################################################################

    def on_global_legato_changed(self, state: bool) -> None:
        self.settings = replace(self.settings, global_legato=state)
        self.update_status(f"Global legato {endis(state)}")

    ###########################################################################

    def on_global_volume_changed(self, val: int | str) -> None:
        setting = parse_setting(val)
        self.settings = replace(self.settings, global_volume=setting)
        self.update_status(f"Global volume set to {setting}")

    ###########################################################################

    def on_interpolate_changed(self, state: bool) -> None:
        with suppress(NoSample):
            sample_idx = self.state.sample_idx
            sample_name = sample_idx[1] or sample_idx[0]

            self._update_sample_state(dyn_interpolate=state)
            self.update_status(
                f"Dynamics interpolation for {sample_name} {endis(state)}"
            )

    ###########################################################################

    def on_load(self, fname: Path) -> None:
        try:
            project, backup_fname = Project.load(fname)
            if backup_fname is not None:
                self.response_generated.emit(
                    False,
                    "Old File",
                    "This project uses an old save file format.  "
                    "We've tried our best to upgrade, but there might still "
                    "be some problems.  Your old save file was backed up as "
                    f"{backup_fname}, you should probably keep a copy until "
                    "you've confirmed the upgrade was successful.  Or fixed "
                    "any problems with it, it's all the same to SPaCeMusicW.",
                )

        except SmwMusicException as e:
            self.response_generated.emit(True, "Invalid save version", str(e))
        except FileNotFoundError:
            self.response_generated.emit(
                True, "Invalid project file", "Could not find project file"
            )
        else:
            self._append_recent_project(fname)

            self._load_musicxml(project)

            self.reinforce_state()
            self.update_status(f"Opened project {self.info.project_name}")

    ###########################################################################

    def on_loop_analysis_changed(self, enabled: bool) -> None:
        self.settings = replace(self.settings, loop_analysis=enabled)
        self.update_status(f"Loop analysis {endis(enabled)}")

    ###########################################################################

    def on_measure_numbers_changed(self, enabled: bool) -> None:
        self.settings = replace(self.settings, measure_numbers=enabled)
        self.update_status(f"Measure # reporting {endis(enabled)}")

    ###########################################################################

    def on_multisample_sample_add_clicked(
        self, name: str, notes: str, notehead: str, output: str, track: bool
    ) -> None:
        self._multisample_changed(True, name, notes, notehead, output, track)

    ###########################################################################

    def on_multisample_sample_changed(
        self, name: str, notes: str, notehead: str, output: str, track: bool
    ) -> None:
        self._multisample_changed(False, name, notes, notehead, output, track)

    ###########################################################################

    def on_multisample_sample_remove_clicked(self) -> None:
        state = self.state
        with suppress(NoSample):
            inst, sample = state.sample_idx
            if sample:
                instruments = deepcopy(state.project.settings.instruments)
                keys = sorted(instruments[inst].multisamples.keys())
                instruments[inst].multisamples.pop(sample)

                idx = keys.index(sample)
                try:
                    new_inst = keys[idx + 1]
                except IndexError:
                    new_inst = keys[idx - 1] if idx else ""

                # TODO: Replace
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
        self.update_status(f"Pan {endis(state)}")

    ###########################################################################

    def on_pan_invert_changed(self, left: bool, state: bool) -> None:
        with suppress(NoSample):
            pan_setting = list(self.state.sample.pan_invert)
            pan_setting[0 if left else 1] = state

            self._update_sample_state(
                pan_invert=(pan_setting[0], pan_setting[1])
            )
            self.update_status(
                f'Pan {"left" if left else "right"} inversion {endis(state)}'
            )

    ###########################################################################

    def on_pan_setting_changed(self, val: int) -> None:
        self._update_sample_state(pan_setting=val)
        self.update_status(f"Pan changed to {val}")

    ###########################################################################

    def on_play_spc_clicked(self) -> None:
        spc = amk.spc_fname(self.state.project)

        if not spc.exists():
            self.response_generated.emit(
                True, "SPC Play", "SPC file doesn't exist"
            )
        else:
            spcplay.play(self.preferences.spcplay_fname, spc)

        self.update_status("SPC played")

    ###########################################################################

    def on_recent_projects_cleared(self) -> None:
        spcmw.save_recent_projects([])
        self.update_status("Recent projects cleared")

    ###########################################################################

    def on_redo_clicked(self) -> None:
        if self._undo_level > 0:
            self._undo_level -= 1
            self._signal_state_change()
            self.update_status("Redo")

    ###########################################################################

    def on_reload_musicxml_clicked(self) -> None:
        # self._load_musicxml(self.info.musicxml_fname, True)
        self._reload_musicxml(self.info.musicxml_fname, True)

        self.reinforce_state()
        self.update_status("MusicXML reloaded")

    ###########################################################################

    def on_render_zip_clicked(self) -> None:
        self.update_status("Zip file generated")
        zname = amk.render_zip(self.state.project)
        self.response_generated.emit(
            False, "Zip Render", f"Zip file {zname} rendered"
        )

    ###########################################################################

    def on_sample_changed(self, sample_idx: tuple[str, str]) -> None:
        self.state = replace(self.state, sample_idx=sample_idx)

        inst, sample = sample_idx
        name = sample or inst
        self.update_status(f"{name} selected")

    ###########################################################################

    def on_sample_opt_selected(
        self, group: BuiltinSampleGroup, checked: bool
    ) -> None:
        if checked:
            self.settings = replace(self.settings, builtin_sample_group=group)
            self.update_status(f"Builtin group set to {group}")

    ###########################################################################

    def on_sample_opt_source_changed(
        self, idx: int, source: BuiltinSampleSource
    ) -> None:
        sources = self.settings.builtin_sample_sources.copy()
        sources[idx] = source
        self.settings = replace(self.settings, builtin_sample_sources=sources)
        self.update_status(f"Builtin sample {idx:02x} set to {source}")

    ###########################################################################

    def on_save(self) -> None:
        self._save_backup()

        self.project.save()
        self.saved = True
        self.reinforce_state()
        self.update_status("Project saved")

    ###########################################################################

    def on_select_adsr_mode_selected(self, state: bool) -> None:
        self._update_envelope_state(adsr_mode=state)
        self.update_status(
            f"Envelope mode set to {'ADSR' if state else 'Gain'}"
        )

    ###########################################################################

    def on_solomute_changed(
        self, sample_idx: tuple[str, str], solo: bool, state: bool
    ) -> None:
        inst_name, sample_name = sample_idx
        instruments = deepcopy(self.settings.instruments)
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

        self.settings = replace(self.settings, instruments=instruments)

        self.update_status(f"{msg} {field} {endis(state)}")

    ###########################################################################

    def on_start_measure_changed(self, value: int) -> None:
        section_idx = 0
        for idx, sec_measure in enumerate(self.song.rehearsal_marks.values()):
            if sec_measure <= value:
                # Plus one because there's a default first section which the
                # enumeration doesn't account for
                section_idx = idx + 1

        self.state = replace(
            self.state, start_measure=value, start_section_idx=section_idx
        )
        self.update_status(f"Start measure set to {value}")

    ###########################################################################

    def on_start_section_activated(self, section_idx: int) -> None:
        name = self.state.section_names[section_idx]

        if section_idx == 0:
            measure = 1
        else:
            measures = list(self.song.rehearsal_marks.values())
            measure = measures[section_idx - 1]

        self.state = replace(
            self.state, start_measure=measure, start_section_idx=section_idx
        )
        self.update_status(f"Start section set to {name}")

    ###########################################################################

    def on_subtune_changed(self, val: int | str) -> None:
        setting = parse_setting(val)
        self._update_sample_state(subtune_setting=setting)
        self.update_status(f"Subtune set to {setting}")

    ###########################################################################

    def on_superloop_analysis_changed(self, enabled: bool) -> None:
        self.settings = replace(self.settings, superloop_analysis=enabled)
        self.update_status(f"Superloop analysis {endis(enabled)}")

    ###########################################################################

    def on_sus_level_changed(self, val: int | str) -> None:
        setting = parse_setting(val, 7)
        self._update_envelope_state(sus_level_setting=setting, adsr_mode=True)
        self.update_status(f"Sustain level set to {setting}")

    ###########################################################################

    def on_sus_rate_changed(self, val: int | str) -> None:
        setting = parse_setting(val, 31)
        self._update_envelope_state(sus_rate_setting=setting, adsr_mode=True)
        self.update_status(f"Decay rate set to {setting}")

    ###########################################################################

    def on_tune_changed(self, val: int | str) -> None:
        setting = parse_setting(val)
        self._update_sample_state(tune_setting=setting)
        self.update_status(f"Tune set to {setting}")

    ###########################################################################

    def on_tuning_sample_freq_changed(self, setting: str) -> None:
        with suppress(ValueError, NoSample):
            freq = float(setting)
            tuning = replace(self.state.sample.tuning, sample_freq=freq)
            self._update_sample_state(tuning=tuning)
            self.update_status(f"Using sampling frequency {freq}Hz")

    ###########################################################################

    def on_tuning_manual_freq_changed(self, setting: str) -> None:
        with suppress(ValueError, NoSample):
            freq = float(setting)
            tuning = replace(self.state.sample.tuning, frequency=freq)
            self._update_sample_state(tuning=tuning)
            self.update_status(f"Using manual tuning frequency {freq}Hz")

    ###########################################################################

    def on_tuning_manual_note_changed(
        self, pitch_class: int, octave: int
    ) -> None:
        with suppress(NoSample):
            pitch = Pitch(octave=octave, pitchClass=pitch_class)
            tuning = replace(self.state.sample.tuning, pitch=pitch)
            self._update_sample_state(tuning=tuning)
            self.update_status(f"Target pitch set to {pitch.nameWithOctave}")

    ###########################################################################

    def on_tuning_output_note_changed(
        self, pitch_class: int, octave: int
    ) -> None:
        with suppress(NoSample):
            pitch = Pitch(octave=octave, pitchClass=pitch_class)
            tuning = replace(self.state.sample.tuning, output=pitch)
            self._update_sample_state(tuning=tuning)
            self.update_status(f"Target output set to {pitch.nameWithOctave}")

    ###########################################################################

    def on_tuning_semitone_shift_changed(self, shift: int) -> None:
        with suppress(NoSample):
            tuning = replace(self.state.sample.tuning, semitone_shift=shift)
            self._update_sample_state(tuning=tuning)
            self.update_status(f"Set semitone shift to {shift}")

    ###########################################################################

    def on_tuning_use_auto_freq_selected(self, state: bool) -> None:
        with suppress(NoSample):
            if state:
                tuning = replace(
                    self.state.sample.tuning, source=TuneSource.AUTO
                )
                self._update_sample_state(tuning=tuning)
                self.update_status("Using auto frequency tuning")

    ###########################################################################

    def on_tuning_use_manual_freq_selected(self, state: bool) -> None:
        with suppress(NoSample):
            if state:
                tuning = replace(
                    self.state.sample.tuning, source=TuneSource.MANUAL_FREQ
                )
                self._update_sample_state(tuning=tuning)
                self.update_status("Using manual frequency tuning")

    ###########################################################################

    def on_tuning_use_manual_note_selected(self, state: bool) -> None:
        with suppress(NoSample):
            if state:
                tuning = replace(
                    self.state.sample.tuning, source=TuneSource.MANUAL_NOTE
                )
                self._update_sample_state(tuning=tuning)
                self.update_status("Using manual note tuning")

    ###########################################################################

    def on_undo_clicked(self) -> None:
        if self._undo_level < len(self._history) - 1:
            self._undo_level += 1
            self._signal_state_change()
            self.update_status("Undo")

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _append_recent_project(self, fname: Path) -> None:
        fname = fname.resolve()
        history = spcmw.get_recent_projects()
        if fname in history:
            history.remove(fname)
        history.append(fname)
        spcmw.save_recent_projects(history)
        self.recent_projects_updated.emit(spcmw.get_recent_projects())

    ###########################################################################

    def _check_first_use(self) -> None:
        if spcmw.first_use():
            msg = "Welcome, and thank you for trying SPaCeMusicW."
            msg += "\n\nIt looks like this is your first time using the tool."
            msg += "\nWe recommend reading through our getting started guide"
            msg += "\nor watching our tutorials at:"
            msg += "\nhttps://www.youtube.com/playlist?"
            msg += "list=PL7ql3YAGsvzHoIEAaDQqvVE3Jlke_nVo7"

            self.response_generated.emit(
                False, "It's dangerous to go alone!  Take this.", msg
            )

    ###########################################################################

    def _check_for_updates(self) -> None:
        if self.preferences.release_check:
            release = newest_release()
            if release is not None and release[1] > version_tuple(__version__):
                url, version = release
                self.response_generated.emit(
                    False,
                    "New Version",
                    f"SPaCeMusicW <a href={url}>v{version}</a> is available "
                    + "for download<br />Version checking can be disabled "
                    + "in preferences",
                )

    ###########################################################################

    def _emit_quote(self) -> None:
        quote: tuple[str, str] = choice(quotes)  # nosec: B311
        self.update_status(f"{quote[1]}: {quote[0]}")

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

    def _load_musicxml(self, project: Project) -> None:
        self._reset_state(project)

        musicxml = project.info.musicxml_fname
        if musicxml is None:
            self._reset_song()
            return

        try:
            self.song = Song.from_music_xml(musicxml)
        except SongException as e:
            self.response_generated.emit(
                True,
                "Error loading score",
                f"Could not open score {musicxml}: {str(e)}",
            )
        else:
            self.settings = replace(
                self.settings, instruments=extract_instruments(self.song)
            )

            self.songinfo_changed.emit("TODO")
            self.saved = True

            # TODO: Re-add this
            # if self._on_generate_mml_clicked(False):
            #     self._on_generate_spc_clicked(False)

    ###########################################################################

    def _reload_musicxml(self) -> None:
        musicxml = self.info.musicxml_fname
        if musicxml is None:
            self._reset_song()
            return

        try:
            self.song = Song.from_music_xml(musicxml)
        except SongException as e:
            self.response_generated.emit(
                True,
                "Error loading score",
                f"Could not open score {musicxml}: {str(e)}",
            )
        else:
            self.songinfo_changed.emit("")
            if keep_inst_settings:
                # Reconcile instrument settings
                for inst_name, song_inst in self.song.instruments.items():
                    with suppress(KeyError):
                        state_inst = self.settings.instruments[inst_name]
                        song_inst.solo = state_inst.solo
                        song_inst.mute = state_inst.mute
                        song_inst.samples = state_inst.samples

            self.settings.instruments = deepcopy(self.song.instruments)

            self.state.start_section_idx = 0

            if self._on_generate_mml_clicked(False):
                self._on_generate_spc_clicked(False)

    ###########################################################################

    def _load_prefs(self) -> None:
        self.preferences = get_preferences()

        self._start_watcher()

        # TODO: Update this
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

        # TODO
        self._update_sample_state(
            envelope=params.envelope,
            tune_setting=params.tuning,
            subtune_setting=params.subtuning,
        )

    ###########################################################################

    def _multisample_changed(
        self,
        new: bool,
        name: str,
        notes: str,
        notehead: str,
        output: str,
        track: bool,
    ) -> None:
        state = self.state

        # All the inputs need to be present to continue
        if not all([name, notes, notehead, output]):
            return

        # Make sure we've got an instrument selected
        with suppress(NoSample):
            sample = state.sample

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
                ulim=ulim, llim=llim, notehead=head, start=start, track=track
            )
        else:
            sample = replace(
                sample,
                llim=llim,
                ulim=ulim,
                start=start,
                notehead=head,
                track=track,
            )

        inst, _ = state.sample_idx

        instruments = deepcopy(state.project.settings.instruments)
        instruments[inst].multisamples[name] = sample
        # TODO: Replace                                                                      # T
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
        title = "MML Generation"
        error = True

        try:
            MmlExporter.export_project(self.state.project)
        except SongException as e:
            msg = str(e)
        else:
            bad_samples = self._check_bad_tune()
            if bad_samples:
                msg = "\n".join(
                    f"{inst}{f':{samp}' if samp else ''} has 0.0 tuning"
                    for inst, samp in bad_samples
                )
            else:
                error = False
                msg = "Done"

        if report or error:
            self.response_generated.emit(error, title, msg)

        return not error

    ###########################################################################

    def _on_generate_spc_clicked(self, report: bool = True) -> bool:
        error = False
        msg = ""

        try:
            msg = amk.generate_spc(
                self.state.project,
                self._sample_packs,
                self.preferences.convert_timeout,
            )
        except SmwMusicException as e:
            error = True
            msg = e.args[0]

        if report or error:
            self.response_generated.emit(error, "SPC Generated", msg)
            self.update_status("SPC generated")

        if not error:
            self._update_utilization_from_amk()
            self.reinforce_state()

        return not error

    ###########################################################################

    def _reset_state(self, project: Project | None = None) -> None:
        self._history = []
        self._undo_level = 0
        self.state = State(project)

    ###########################################################################

    def _reset_song(self) -> None:
        self._song = None

    ###########################################################################

    def _rollback_undo(self) -> None:
        while self._undo_level:
            self._history.pop()
            self._undo_level -= 1

    ###########################################################################

    def _save_backup(self) -> None:
        self.state.project.save(backup=True)

    ###########################################################################

    def _select_gain(self, state: bool, mode: GainMode, caption: str) -> None:
        if state:
            kwargs: dict[str, GainMode | int | bool] = {
                "gain_mode": mode,
                "adsr_mode": False,
            }
            with suppress(NoSample):
                kwargs["gain_setting"] = min(
                    31, self.state.sample.envelope.gain_setting
                )

            # TODO: address this mypy error
            self._update_envelope_state(**kwargs)
            self.update_status(f"{caption} envelope selected")

    ###########################################################################

    def _signal_state_change(self) -> None:
        # self._signal_state_change_helper(update_instruments, state_change)
        self.state_changed.emit()

    ###########################################################################

    def _signal_state_change_helper(
        self, update_instruments: bool = False, state_change: bool = True
    ) -> None:
        state = self.state

        self.saved = not state_change
        state.unmapped = set()

        self._update_aram_util()

        brr: Brr | None = None
        with suppress(NoSample):
            sample = self.state.sample
            match sample.sample_source:
                case SampleSource.SAMPLEPACK:
                    pack, path = sample.pack_sample
                    brr = self._sample_packs[pack][path].brr
                case SampleSource.BRR:
                    with suppress(FileNotFoundError):
                        brr = Brr.from_file(sample.brr_fname)

        if brr is not None:
            tuning = self.state.sample.tuning
            scale = SAMPLE_FREQ / tuning.sample_freq
            source = tuning.source

            # When not in advanced mode, always use auto tuning
            if not self.preferences.advanced_mode:
                source = TuneSource.AUTO

            match source:
                case TuneSource.AUTO:
                    fundamental = brr.fundamental
                    fundamental /= 2 ** (tuning.semitone_shift / 12)
                case TuneSource.MANUAL_NOTE:
                    fundamental = tuning.pitch.frequency * scale
                case TuneSource.MANUAL_FREQ:
                    fundamental = tuning.frequency * scale

            self.state.calculated_tune = (
                brr.fundamental,
                brr.tune(
                    midi_to_nspc(Pitch("C", octave=4).midi),
                    tuning.output.frequency,
                    fundamental,
                ),
            )
        else:
            self.state.calculated_tune = (0, (0, 0))

        with suppress(NoSong):
            if self.song:
                name = state.sample_idx[0]

                unmapped = self.song.unmapped_notes(
                    name, state.project.settings.instruments[name]
                )

                self.state.unmapped = {
                    (pitch, str(head)) for pitch, head in unmapped
                }

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

    def _update_envelope_state(self, **kwargs: bool | int | GainMode) -> None:
        # TODO: remove ignore
        new_env = replace(self.state.sample.envelope, **kwargs)  # type: ignore
        self._update_sample_state(envelope=new_env)

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
        | Tuning
        | Envelope,
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
        new_state: State,
    ) -> None:
        do_update = True
        if new_state == self.state:
            do_update = False

        if do_update:
            self._rollback_undo()

            # TODO
            # self._save_backup()
            self._signal_state_change()

    ###########################################################################

    def _update_aram_util(self) -> None:
        state = self.state
        aram_util = state.aram_util

        delay = state.project.settings.echo.delay
        aram_util.echo, aram_util.echo_pad = echo_bytes(delay)

        aram_util.samples += self.sample_bytes - state.aram_custom_sample_b

        state.aram_custom_sample_b = self.sample_bytes

    ###########################################################################

    def _update_utilization_from_amk(self) -> None:
        self.state.aram_util = amk.utilization(self.state.project)
        self.state.aram_custom_sample_b = self.sample_bytes

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def echo(self) -> EchoConfig:
        return self.settings.echo

    ###########################################################################

    @echo.setter
    def echo(self, val: EchoConfig) -> None:
        self.settings = replace(self.settings, echo=val)

    ###########################################################################

    @property
    def info(self) -> ProjectInfo:
        return self.project.info

    ###########################################################################

    @info.setter
    def info(self, val: ProjectInfo) -> None:
        self.project = replace(self.project, info=val)

    ###########################################################################

    @property
    def loaded(self) -> bool:
        return self.state.loaded

    ###########################################################################

    @property
    def project(self) -> Project:
        return self.state.project

    ###########################################################################

    @project.setter
    def project(self, val: Project) -> None:
        # Any time we get a new project object, mark unsaved
        if val != self.project:
            self.saved = False
        self.state = replace(self.state, _project=val)

    ###########################################################################

    @property
    def sample_bytes(self) -> int:
        handled: list[tuple[bool, str, Path]] = []

        total_size = 0
        # TODO: Unify sample size calcs
        for sample in self.settings.samples.values():
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
    def settings(self) -> ProjectSettings:
        return self.project.settings

    ###########################################################################

    @settings.setter
    def settings(self, val: ProjectSettings) -> None:
        self.project = replace(self.project, settings=val)

    ###########################################################################

    @property
    def song(self) -> Song:
        if self._song is None:
            raise NoSong()
        return self._song

    ###########################################################################

    @song.setter
    def song(self, val: Song) -> None:
        self._song = val

    ###########################################################################

    @property
    def state(self) -> State:
        return self._history[-1 - self._undo_level]

    ###########################################################################

    @state.setter
    def state(self, val: State) -> None:
        do_update = (self._history == []) or (val != self.state)

        if do_update:
            self._rollback_undo()

            # TODO
            # self._save_backup()
            self._history.append(val)
            self._signal_state_change()
