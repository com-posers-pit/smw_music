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
from dataclasses import fields, replace
from glob import glob
from pathlib import Path
from random import choice
from typing import Callable, TypedDict, Unpack

# Library imports
from music21.pitch import Pitch, PitchException
from PyQt6.QtCore import QObject, pyqtSignal
from watchdog import observers

# Package imports
import smw_music.spcmw as spcmw
from smw_music.common import SmwMusicException, __version__
from smw_music.exporters.mml import MmlExporter
from smw_music.ext_tools import spcplay
from smw_music.ext_tools.amk import (
    ARTIC_DUR_LIM,
    ARTIC_VOL_LIM,
    BuiltinSampleGroup,
    BuiltinSampleSource,
    Utilization,
    default_utilization,
)
from smw_music.song import NoteHead, Song, SongException
from smw_music.spc700 import (
    SAMPLE_FREQ,
    Brr,
    EchoConfig,
    Envelope,
    GainMode,
    SamplePlayer,
    echo_bytes,
    limits,
    midi_to_nspc,
)
from smw_music.spcmw import (
    Artic,
    ArticSetting,
    Dynamics,
    InstrumentConfig,
    InstrumentSample,
    Preferences,
    Project,
    ProjectInfo,
    ProjectSettings,
    SamplePack,
    SampleParams,
    SampleSource,
    TuneSource,
    Tuning,
    advanced,
    amk,
    extract_instruments,
    get_preferences,
    unmapped_notes,
)
from smw_music.utils import brr_size_b, newest_release, version_tuple

from .quotes import quotes
from .sample_packs import SamplePackWatcher
from .state import NoProject, NoSample, State
from .utils import endis, parse_setting

###############################################################################
# Private Class Definitions
###############################################################################


class _EchoT(TypedDict, total=False):
    vol_mag: tuple[float, float]
    vol_inv: tuple[bool, bool]
    delay: int
    fb_mag: float
    fb_inv: bool
    fir_filt: int


###############################################################################


class _EnvelopeT(TypedDict, total=False):
    adsr_mode: bool
    attack_setting: int
    decay_setting: int
    sus_level_setting: int
    sus_rate_setting: int
    gain_mode: GainMode
    gain_setting: int


###############################################################################


class _ProjectT(TypedDict, total=False):
    pass


###############################################################################


class _SampleParamsT(TypedDict, total=False):
    envelope: Envelope
    tuning: int
    subtuning: int


###############################################################################


class _SampleT(TypedDict, total=False):
    default_octave: int
    octave_shift: int
    dynamics: dict[Dynamics, int]
    dyn_interpolate: bool
    artics: dict[Artic, ArticSetting]
    pan_enabled: bool
    pan_setting: int
    pan_invert: tuple[bool, bool]
    sample_source: SampleSource
    builtin_sample_index: int
    pack_sample: tuple[str, Path]
    brr_fname: Path
    params: SampleParams
    mute: bool
    solo: bool
    llim: Pitch
    ulim: Pitch
    notehead: NoteHead
    start: Pitch
    tuning: Tuning
    track: bool
    echo: bool


###############################################################################


class _SettingsT(TypedDict, total=False):
    loop_analysis: bool
    superloop_analysis: bool
    measure_numbers: bool
    start_measure: int
    instruments: dict[str, InstrumentConfig]
    global_volume: int
    global_legato: bool
    global_echo: bool
    echo: EchoConfig
    builtin_sample_group: BuiltinSampleGroup
    builtin_sample_sources: list[BuiltinSampleSource]
    adv_settings: dict[str, advanced.Advanced]


###############################################################################


class _StateT(TypedDict, total=False):
    _project: Project | None
    start_measure: int
    start_section_idx: int
    unmapped: set[tuple[Pitch, str]]
    aram_util: Utilization
    aram_custom_sample_b: int
    calculated_tune: tuple[float, tuple[int, float]]
    section_names: list[str]
    _sample_idx: tuple[str, str] | None


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
    _sample_watcher: observers.Observer

    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self) -> None:
        super().__init__()
        self.preferences = get_preferences()
        self.saved = True
        self._check_amk = False
        self._reset_song()
        self._reset_state()
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

        self._set_info(f"Change {', '.join(changed)}", info)

    ###########################################################################

    def update_sample_packs(self) -> None:
        self._sample_packs = {}

        # TODO: Make this work with folders.
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
        msg = f"Tune setting set to {tune}.{subtune}"
        self._update_sample_params_state(msg, tuning=tune, subtuning=subtune)

    ###########################################################################

    def on_artic_length_changed(self, artic: Artic, val: int | str) -> None:
        with suppress(NoSample):
            artics = deepcopy(self.state.sample.artics)
            artics[artic].length = parse_setting(val, ARTIC_DUR_LIM)
            msg = f"{artic} length set to {val}"
            self._update_sample_state(msg, artics=artics)

    ###########################################################################

    def on_artic_volume_changed(self, artic: Artic, val: int | str) -> None:
        with suppress(NoSample):
            artics = deepcopy(self.state.sample.artics)
            artics[artic].volume = parse_setting(val, ARTIC_VOL_LIM)
            msg = f"{artic} volume set to {val}"
            self._update_sample_state(msg, artics=artics)

    ###########################################################################

    def on_attack_changed(self, val: int | str) -> None:
        setting = parse_setting(val, limits.ADSR_ATT)
        msg = f"Attack set to {setting}"
        self._update_envelope(msg, attack_setting=setting, adsr_mode=True)

    ###########################################################################

    def on_audition_start(self, audition_note: str) -> None:
        with suppress(NoSample):
            sample = self.state.sample
            params = sample.params
            tune = 256 * params.tuning + params.subtuning
            note = midi_to_nspc(Pitch(audition_note).midi)

            play = False
            target: Callable[
                [bytes, Envelope, int, int, int], None
            ] | Callable[[Path, Envelope, int, int, int], None]
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
                    target=target, args=(arg, params.envelope, tune, note, 0)
                )
                self._sample_player_th.start()

    ###########################################################################

    def on_audition_stop(self) -> None:
        self._sample_player.stop()

    ###########################################################################

    def on_brr_fname_changed(self, fname: str) -> None:
        msg = f"BRR set to {fname}"
        self._update_sample_state(
            msg, brr_fname=Path(fname), sample_source=SampleSource.BRR
        )

    ###########################################################################

    def on_brr_sample_selected(self, state: bool) -> None:
        if state:
            msg = "Sample source set to BRR"
            self._update_sample_state(msg, sample_source=SampleSource.BRR)

    ###########################################################################

    def on_brr_setting_changed(self, val: str) -> None:
        # Spoof the expected pattern format
        val = f'""{val}'
        _, params = SampleParams.from_pattern(val)
        msg = f"BRR setting changed to {val}"
        self._update_sample_state(msg, params=params)

    ###########################################################################

    def on_builtin_sample_changed(self, index: int) -> None:
        msg = f"Builtin sample {index} selected"
        self._update_sample_state(
            msg, builtin_sample_index=index, sample_source=SampleSource.BUILTIN
        )

    ###########################################################################

    def on_builtin_sample_selected(self, state: bool) -> None:
        if state:
            msg = "Sample source set to builtin"
            self._update_sample_state(msg, sample_source=SampleSource.BUILTIN)

    ###########################################################################

    def on_decay_changed(self, val: int | str) -> None:
        setting = parse_setting(val, limits.ADSR_DEC)
        msg = f"Decay set to {setting}"
        self._update_envelope(msg, decay_setting=setting, adsr_mode=True)

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
                msg = f"Dynamics {level} set to {setting}"
                self._update_sample_state(msg, dynamics=dynamics)

    ###########################################################################

    def on_echo_feedback_changed(self, val: int | str) -> None:
        setting = parse_setting(val, 128) / 128
        msg = f"Echo feedback magnitude set to {setting}"
        self._update_echo(msg, fb_mag=setting)

    ###########################################################################

    def on_echo_feedback_surround_changed(self, state: bool) -> None:
        msg = f"Echo feedback surround {endis(state)}"
        self._update_echo(msg, fb_inv=state)

    ###########################################################################

    def on_echo_left_changed(self, val: int | str) -> None:
        setting = parse_setting(val, 128) / 128
        msg = f"Echo left channel magnitude set to {setting}"
        self._update_echo(msg, vol_mag=(setting, self.echo.vol_mag[1]))

    ###########################################################################

    def on_echo_left_surround_changed(self, state: bool) -> None:
        msg = f"Echo left channel surround {endis(state)}"
        self._update_echo(msg, vol_inv=(state, self.echo.vol_inv[1]))

    ###########################################################################

    def on_echo_right_changed(self, val: int | str) -> None:
        setting = parse_setting(val, 128) / 128
        msg = f"Echo right channel magnitude set to {setting}"
        self._update_echo(msg, vol_mag=(self.echo.vol_mag[0], setting))

    ###########################################################################

    def on_echo_right_surround_changed(self, state: bool) -> None:
        msg = f"Echo right channel surround {endis(state)}"
        self._update_echo(msg, vol_inv=(self.echo.vol_inv[0], state))

    ###########################################################################

    def on_echo_delay_changed(self, val: int | str) -> None:
        setting = parse_setting(val, limits.ECHO_DELAY)
        self._update_echo(f"Echo delay changed to {val}", delay=setting)

    ###########################################################################

    def on_filter_0_toggled(self, state: bool) -> None:
        fir_filt = 0 if state else 1
        self._update_echo(f"Echo filter set to {fir_filt}", fir_filt=fir_filt)

    ###########################################################################

    def on_gain_declin_selected(self, state: bool) -> None:
        self._select_gain(state, GainMode.DECLIN, "Decreasing linear")

    ###########################################################################

    def on_gain_decexp_selected(self, state: bool) -> None:
        self._select_gain(state, GainMode.DECEXP, "Decreasing exponential")

    ###########################################################################

    def on_gain_direct_selected(self, state: bool) -> None:
        if state:
            msg = "Direct gain envelope selected"
            self._update_envelope(
                msg, gain_mode=GainMode.DIRECT, adsr_mode=False
            )

    ###########################################################################

    def on_gain_incbent_selected(self, state: bool) -> None:
        self._select_gain(state, GainMode.INCBENT, "Increasing bent")

    ###########################################################################

    def on_gain_inclin_selected(self, state: bool) -> None:
        self._select_gain(state, GainMode.INCLIN, "Increasing linear")

    ###########################################################################

    def on_gain_changed(self, val: int | str) -> None:
        with suppress(NoSample):
            mode = self.state.sample.params.envelope.gain_mode
            lim = (
                limits.DIRECT_GAIN if mode == GainMode.DIRECT else limits.GAIN
            )
            setting = parse_setting(val, lim)
            msg = "Gain setting changed to {setting}"
            self._update_envelope(msg, gain_setting=setting, adsr_mode=False)

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
        self._update_settings(f"Echo {endis(state)}", global_echo=state)

    ###########################################################################

    def on_global_legato_changed(self, state: bool) -> None:
        msg = f"Global legato {endis(state)}"
        self._update_settings(msg, global_legato=state)

    ###########################################################################

    def on_global_volume_changed(self, val: int | str) -> None:
        setting = parse_setting(val)
        msg = f"Global volume set to {setting}"
        self._update_settings(msg, global_volume=setting)

    ###########################################################################

    def on_interpolate_changed(self, state: bool) -> None:
        with suppress(NoSample):
            sample_idx = self.state.sample_idx
            sample_name = sample_idx[1] or sample_idx[0]

            msg = f"Dynamics interpolation for {sample_name} {endis(state)}"
            self._update_sample_state(msg, dyn_interpolate=state)

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
            self.saved = True

            self.update_status(f"Opened project {self.info.project_name}")

    ###########################################################################

    def on_loop_analysis_changed(self, enabled: bool) -> None:
        msg = f"Loop analysis {endis(enabled)}"
        self._update_settings(msg, loop_analysis=enabled)

    ###########################################################################

    def on_make_drumset_clicked(self) -> None:
        inst = self.state.instrument
        instrument = InstrumentConfig.make_percussion(
            **{k.name: getattr(inst, k.name) for k in fields(inst)}
        )
        msg = f"Converted {self.state.sample_idx[0]} to drumset"
        self._set_state(msg, self.state.replace_instrument(instrument))

    ###########################################################################

    def on_measure_numbers_changed(self, enabled: bool) -> None:
        msg = f"Measure # reporting {endis(enabled)}"
        self._update_settings(msg, measure_numbers=enabled)

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
                instruments = deepcopy(self.settings.instruments)
                keys = sorted(instruments[inst].multisamples.keys())
                instruments[inst].multisamples.pop(sample)

                idx = keys.index(sample)
                try:
                    new_inst = keys[idx + 1]
                except IndexError:
                    new_inst = keys[idx - 1] if idx else ""

                # TODO: Verify this is right
                settings = replace(self.settings, instruments=instruments)
                project = replace(self.project, settings=settings)
                msg = f"Removed sample {sample} from instrument {inst}"
                self._update_state(
                    msg, _project=project, _sample_idx=(inst, new_inst)
                )

    ###########################################################################

    def on_multisample_sample_selected(self, state: bool) -> None:
        return
        # TODO
        # if state:
        #     self._update_sample_state(sample_source=SampleSource.MULTISAMPLE)
        #     self.update_status("Sample source set to multisample")

    ###########################################################################

    def on_octave_shift_changed(self, octave_shift: int) -> None:
        msg = f"Octave set to {octave_shift}"
        self._update_sample_state(msg, octave_shift=octave_shift)

    ###########################################################################

    def on_pack_sample_changed(self, item_id: tuple[str, Path]) -> None:
        msg = f"Sample pack {item_id[0]}:{str(item_id[1])} selected"
        self._update_sample_state(
            msg, pack_sample=item_id, sample_source=SampleSource.SAMPLEPACK
        )
        self._load_sample_settings(item_id)

    ###########################################################################

    def on_pack_sample_selected(self, state: bool) -> None:
        with suppress(NoSample):
            if state:
                msg = "Sample source set to sample pack"
                self._update_sample_state(
                    msg, sample_source=SampleSource.SAMPLEPACK
                )
                sample = self.state.sample.pack_sample
                if sample[0]:
                    self._load_sample_settings(sample)

    ###########################################################################

    def on_pan_enable_changed(self, state: bool) -> None:
        self._update_sample_state(f"Pan {endis(state)}", pan_enabled=state)

    ###########################################################################

    def on_pan_invert_changed(self, left: bool, state: bool) -> None:
        with suppress(NoSample):
            pan_setting = list(self.state.sample.pan_invert)
            pan_setting[0 if left else 1] = state

            msg = f'Pan {"left" if left else "right"} inversion {endis(state)}'
            self._update_sample_state(
                msg, pan_invert=(pan_setting[0], pan_setting[1])
            )

    ###########################################################################

    def on_pan_setting_changed(self, val: int) -> None:
        self._update_sample_state(f"Pan changed to {val}", pan_setting=val)

    ###########################################################################

    def on_play_spc_clicked(self) -> None:
        spc = amk.spc_fname(self.project)

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
        self._load_musicxml()
        self.update_status("MusicXML reloaded")

    ###########################################################################

    def on_render_zip_clicked(self) -> None:
        self.update_status("Zip file generated")
        zname = amk.render_zip(self.project)
        self.response_generated.emit(
            False, "Zip Render", f"Zip file {zname} rendered"
        )

    ###########################################################################

    def on_sample_changed(self, sample_idx: tuple[str, str]) -> None:
        inst, sample = sample_idx
        name = sample or inst
        self._update_state(f"{name} selected", _sample_idx=sample_idx)

    ###########################################################################

    def on_sample_opt_selected(
        self, group: BuiltinSampleGroup, checked: bool
    ) -> None:
        if checked:
            msg = f"Builtin group set to {group}"
            self._update_settings(msg, builtin_sample_group=group)

    ###########################################################################

    def on_sample_opt_source_changed(
        self, idx: int, source: BuiltinSampleSource
    ) -> None:
        sources = self.settings.builtin_sample_sources.copy()
        sources[idx] = source
        self._update_settings(
            f"Builtin sample {idx:02x} set to {source}",
            builtin_sample_sources=sources,
        )

    ###########################################################################

    def on_save(self) -> None:
        self._save_backup()

        self.project.save()
        self.saved = True
        self.reinforce_state()
        self.update_status("Project saved")

    ###########################################################################

    def on_select_adsr_mode_selected(self, state: bool) -> None:
        msg = f"Envelope mode set to {'ADSR' if state else 'Gain'}"
        self._update_envelope(msg, adsr_mode=state)

    ###########################################################################

    # TODO: Look at this
    def on_solomute_changed(
        self, sample_idx: tuple[str, str], solo_sel: bool, state: bool
    ) -> None:
        inst_name, sample_name = sample_idx
        instruments = deepcopy(self.settings.instruments)
        inst = instruments[inst_name]

        solo = inst.solo
        mute = inst.mute
        if solo_sel:
            field = "solo"
            solo = state
        else:
            field = "mute"
            mute = state

        if sample_name:
            msg = f"{inst_name}.{sample_name}"
            inst.multisamples[sample_name] = replace(
                inst.multisamples[sample_name], solo=solo, mute=mute
            )
            # If a sample's solo/mute is being disabled, disable it in the
            # instrument as well
            if not state:
                inst.sample = replace(inst.sample, solo=solo, mute=mute)

        else:
            # Apply an instrument mute/solo to all samples
            msg = f"{inst_name}"
            inst.sample = replace(inst.sample, solo=solo, mute=mute)
            for sample_name, sample in inst.multisamples.items():
                inst.multisamples[sample_name] = replace(
                    sample, solo=solo, mute=mute
                )

        msg = f"{msg} {field} {endis(state)}"
        self._update_settings(msg, instruments=instruments)

    ###########################################################################

    def on_start_measure_changed(self, value: int) -> None:
        section_idx = 0
        for idx, sec_measure in enumerate(self.song.rehearsal_marks.values()):
            if sec_measure <= value:
                # Plus one because there's a default first section which the
                # enumeration doesn't account for
                section_idx = idx + 1

        msg = f"Start measure set to {value}"
        self._update_state(
            msg, start_measure=value, start_section_idx=section_idx
        )

    ###########################################################################

    def on_start_section_activated(self, section_idx: int) -> None:
        name = self.state.section_names[section_idx]

        if section_idx == 0:
            measure = 1
        else:
            measures = list(self.song.rehearsal_marks.values())
            measure = measures[section_idx - 1]

        msg = f"Start section set to {name}"
        self._update_state(
            msg, start_measure=measure, start_section_idx=section_idx
        )

    ###########################################################################

    def on_subtune_changed(self, val: int | str) -> None:
        setting = parse_setting(val)
        msg = f"Subtune set to {setting}"
        self._update_sample_params_state(msg, subtuning=setting)

    ###########################################################################

    def on_superloop_analysis_changed(self, enabled: bool) -> None:
        msg = f"Superloop analysis {endis(enabled)}"
        self._update_settings(msg, superloop_analysis=enabled)

    ###########################################################################

    def on_sus_level_changed(self, val: int | str) -> None:
        setting = parse_setting(val, limits.ADSR_SUS_LEVEL)
        msg = f"Sustain level set to {setting}"
        self._update_envelope(msg, sus_level_setting=setting, adsr_mode=True)

    ###########################################################################

    def on_sus_rate_changed(self, val: int | str) -> None:
        setting = parse_setting(val, limits.ADSR_SUS_RATE)
        msg = f"Decay rate set to {setting}"
        self._update_envelope(msg, sus_rate_setting=setting, adsr_mode=True)

    ###########################################################################

    def on_tune_changed(self, val: int | str) -> None:
        setting = parse_setting(val)
        msg = f"Tune set to {setting}"
        self._update_sample_params_state(msg, tuning=setting)

    ###########################################################################

    def on_tuning_sample_freq_changed(self, setting: str) -> None:
        with suppress(ValueError, NoSample):
            freq = float(setting)
            tuning = replace(self.state.sample.tuning, sample_freq=freq)
            msg = f"Using sampling frequency {freq}Hz"
            self._update_sample_state(msg, tuning=tuning)

    ###########################################################################

    def on_tuning_manual_freq_changed(self, setting: str) -> None:
        with suppress(ValueError, NoSample):
            freq = float(setting)
            tuning = replace(self.state.sample.tuning, frequency=freq)
            msg = f"Using manual tuning frequency {freq}Hz"
            self._update_sample_state(msg, tuning=tuning)

    ###########################################################################

    def on_tuning_manual_note_changed(
        self, pitch_class: int, octave: int
    ) -> None:
        with suppress(NoSample):
            pitch = Pitch(octave=octave, pitchClass=pitch_class)
            tuning = replace(self.state.sample.tuning, pitch=pitch)
            msg = f"Target pitch set to {pitch.nameWithOctave}"
            self._update_sample_state(msg, tuning=tuning)

    ###########################################################################

    def on_tuning_output_note_changed(
        self, pitch_class: int, octave: int
    ) -> None:
        with suppress(NoSample):
            pitch = Pitch(octave=octave, pitchClass=pitch_class)
            tuning = replace(self.state.sample.tuning, output=pitch)
            msg = f"Target output set to {pitch.nameWithOctave}"
            self._update_sample_state(msg, tuning=tuning)

    ###########################################################################

    def on_tuning_semitone_shift_changed(self, shift: int) -> None:
        with suppress(NoSample):
            tuning = replace(self.state.sample.tuning, semitone_shift=shift)
            msg = f"Set semitone shift to {shift}"
            self._update_sample_state(msg, tuning=tuning)

    ###########################################################################

    def on_tuning_use_auto_freq_selected(self, state: bool) -> None:
        with suppress(NoSample):
            if state:
                tuning = replace(
                    self.state.sample.tuning, source=TuneSource.AUTO
                )
                msg = "Using auto frequency tuning"
                self._update_sample_state(msg, tuning=tuning)

    ###########################################################################

    def on_tuning_use_manual_freq_selected(self, state: bool) -> None:
        with suppress(NoSample):
            if state:
                tuning = replace(
                    self.state.sample.tuning, source=TuneSource.MANUAL_FREQ
                )
                msg = "Using manual frequency tuning"
                self._update_sample_state(msg, tuning=tuning)

    ###########################################################################

    def on_tuning_use_manual_note_selected(self, state: bool) -> None:
        with suppress(NoSample):
            if state:
                tuning = replace(
                    self.state.sample.tuning, source=TuneSource.MANUAL_NOTE
                )
                msg = "Using manual note tuning"
                self._update_sample_state(msg, tuning=tuning)

    ###########################################################################

    def on_undo_clicked(self) -> None:
        if self._undo_level < len(self._history) - 1:
            self._undo_level += 1
            self._signal_state_change("Undo")

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

    def _get_section_names(self) -> list[str]:
        section_names: list[str] = []
        with suppress(NoSong):
            section_names = list(self.song.rehearsal_marks.keys())

        return section_names

    ###########################################################################

    def _get_tune(self, state: State) -> tuple[float, tuple[int, float]]:
        brr: Brr | None = None
        with suppress(NoProject, NoSample):
            sample = state.sample
            match sample.sample_source:
                case SampleSource.SAMPLEPACK:
                    pack, path = sample.pack_sample
                    brr = self._sample_packs[pack][path].brr
                case SampleSource.BRR:
                    with suppress(FileNotFoundError):
                        brr = Brr.from_file(sample.brr_fname)

        calculated_tune = (0.0, (0, 0.0))
        if brr is not None:
            tuning = state.sample.tuning
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

            calculated_tune = (
                brr.fundamental,
                brr.tune(
                    midi_to_nspc(Pitch("C", octave=4).midi),
                    tuning.output.frequency,
                    fundamental,
                ),
            )

        return calculated_tune

    ###########################################################################

    def _get_unmapped_notes(self) -> set[tuple[Pitch, str]]:
        unmapped = set()
        with suppress(NoSong, NoSample):
            notes = unmapped_notes(
                self.song, self.state.sample_idx[0], self.state.instrument
            )
            unmapped = {(pitch, str(head)) for pitch, head in notes}

        return unmapped

    ###########################################################################

    def _get_updated_amk_util(self, state: State) -> tuple[Utilization, int]:
        return amk.utilization(state.project), self.sample_bytes

    ###########################################################################

    def _get_updated_util(self, state: State) -> tuple[Utilization, int]:
        util = default_utilization()
        sample_bytes = 0

        with suppress(NoProject):
            # Update the echo bytes in the utilization
            delay = state.project.settings.echo.delay
            echo, echo_pad = echo_bytes(delay)

            # TODO: Verify this logic, I don't think it's right
            # Update the sample size, add the new sample length and remove
            # whatever the previous amount was.
            samples = (
                self.state.aram_util.samples
                + self.sample_bytes  # TODO: fix this
                - self.state.aram_custom_sample_b
            )

            util = replace(
                self.state.aram_util,
                samples=samples,
                echo=echo,
                echo_pad=echo_pad,
            )
            sample_bytes = self.sample_bytes  # TODO: fix this

        return (util, sample_bytes)

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

        self._update_sample_state(None, force_update=True, dynamics=dynamics)

    ###########################################################################

    def _load_musicxml(self, project: Project | None = None) -> None:
        if project is None:
            reload = True
            project = self.project
        else:
            reload = False

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
            instruments = extract_instruments(self.song)
            if reload:
                for k in instruments:
                    with suppress(KeyError):
                        instruments[k] = self.settings.instruments[k]

            # TODO: Update msg
            msg = None
            self._update_settings(msg, instruments=instruments)

            self.songinfo_changed.emit("TODO")

            # TODO: Re-add this
            # if self._on_generate_mml_clicked(False):
            #     self._on_generate_spc_clicked(False)

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

    # TODO: Absorb precursor state update calls
    def _load_sample_settings(self, item_id: tuple[str, Path]) -> None:
        pack, sample_path = item_id
        params = self._sample_packs[pack][sample_path].params

        self._update_sample_params_state(
            None,
            envelope=params.envelope,
            tuning=params.tuning,
            subtuning=params.subtuning,
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

        instruments = deepcopy(self.settings.instruments)
        instruments[inst].multisamples[name] = sample

        # TODO: Review
        settings = replace(self.settings, instruments=instruments)
        project = replace(self.project, settings=settings)
        if new:
            msg = f"Added multisample {name} to {inst}"
        else:
            msg = f"Updated multisample {name} of {inst}"
        self._update_state(msg, _project=project, _sample_idx=(inst, name))

    ###########################################################################

    def _on_generate_mml_clicked(self, report: bool = True) -> bool:
        title = "MML Generation"
        error = True

        try:
            mml = MmlExporter.export_project(self.project)
            error = False
            self.mml_generated.emit(mml)
        except SongException as e:
            msg = str(e)

        if report or error:
            self.response_generated.emit(error, title, msg)

        return not error

    ###########################################################################

    def _on_generate_spc_clicked(self, report: bool = True) -> bool:
        error = False
        msg = ""

        try:
            msg = amk.generate_spc(
                self.project,
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
            self._check_amk = True
            self.reinforce_state()

        return not error

    ###########################################################################

    def _reset_state(self, project: Project | None = None) -> None:
        self._history: list[State] = [State()]
        self._undo_level = 0
        self._set_state(None, State(project))

    ###########################################################################

    def _reset_song(self) -> None:
        self._song: Song | None = None

    ###########################################################################

    def _rollback_undo(self) -> None:
        while self._undo_level:
            self._history.pop()
            self._undo_level -= 1

    ###########################################################################

    def _save_backup(self) -> None:
        with suppress(NoProject):
            self.project.save(backup=True)

    ###########################################################################

    def _select_gain(self, state: bool, mode: GainMode, caption: str) -> None:
        # This shouldn't be called with direct-gain
        assert mode != GainMode.DIRECT

        if state:
            kwargs: _EnvelopeT = {
                "gain_mode": mode,
                "adsr_mode": False,
            }
            with suppress(NoSample):
                kwargs["gain_setting"] = min(
                    limits.GAIN, self.state.sample.params.envelope.gain_setting
                )

            self._update_envelope(f"{caption} envelope selected", **kwargs)

    ###########################################################################

    def _set_echo(self, msg: str | None, echo: EchoConfig) -> None:
        self._update_settings(msg, echo=echo)

    ###########################################################################

    def _set_info(self, msg: str | None, info: ProjectInfo) -> None:
        self._set_project(msg, replace(self.project, info=info))

    ###########################################################################

    def _set_project(self, msg: str | None, project: Project) -> None:
        self._update_state(msg, _project=project)

    ###########################################################################

    def _set_settings(
        self, msg: str | None, settings: ProjectSettings
    ) -> None:
        self._set_project(msg, replace(self.project, settings=settings))

    ###########################################################################

    def _set_state(self, msg: str | None, state: State) -> None:
        if state != self.state:
            with suppress(NoProject):
                if state.project != self.state.project:
                    self.saved = False

            self._rollback_undo()
            self._update_derived_state(state)
            self._save_backup()
            self._signal_state_change(msg)

    ###########################################################################

    def _signal_state_change(self, msg: str | None = None) -> None:
        self.state_changed.emit()
        if msg is not None:
            self.update_status(msg)

    ###########################################################################

    def _start_watcher(self) -> None:
        with suppress(AttributeError):
            if self._sample_watcher.is_alive():
                self._sample_watcher.stop()
                self._sample_watcher.join()

        self._sample_watcher = observers.Observer()
        self._sample_watcher.daemon = True

        self._sample_watcher.schedule(
            SamplePackWatcher(self._update_sample_packs),
            self.preferences.sample_pack_dname,
            False,
        )
        self._sample_watcher.start()

    ###########################################################################

    def _update_derived_state(self, state: State) -> None:
        unmapped = self._get_unmapped_notes()
        section_names = self._get_section_names()
        aram_util, aram_custom_sample_b = self._get_updated_util(state)
        calculated_tune = self._get_tune(state)

        if self._check_amk:
            aram_util, aram_custom_sample_b = self._get_updated_amk_util(state)

        state = replace(
            state,
            unmapped=unmapped,
            aram_util=aram_util,
            aram_custom_sample_b=aram_custom_sample_b,
            calculated_tune=calculated_tune,
            section_names=section_names,
        )

        self._history.append(state)

    ###########################################################################

    def _update_echo(self, msg: str | None, **kwargs: Unpack[_EchoT]) -> None:
        self._set_echo(msg, replace(self.echo, **kwargs))

    ###########################################################################

    def _update_envelope(
        self, msg: str | None, **kwargs: Unpack[_EnvelopeT]
    ) -> None:
        with suppress(NoSample):
            new_env = replace(self.state.sample.params.envelope, **kwargs)
            self._update_sample_params_state(msg, envelope=new_env)

    ###########################################################################

    def _update_sample_packs(self, msg: str) -> None:
        self.update_status(msg)
        self.update_sample_packs()

    ###########################################################################

    def _update_sample_params_state(
        self, msg: str | None, **kwargs: Unpack[_SampleParamsT]
    ) -> None:
        with suppress(NoSample):
            params = replace(self.state.sample.params, **kwargs)
            self._update_sample_state(msg, params=params)

    ###########################################################################

    def _update_sample_state(
        self,
        msg: str | None,
        force_update: bool = False,
        **kwargs: Unpack[_SampleT],
    ) -> None:
        with suppress(NoSample):
            state = self.state
            old_sample = state.sample
            new_sample = replace(old_sample, **kwargs)

            if (new_sample != old_sample) or force_update:
                self._set_state(msg, state.replace_sample(new_sample))

    ###########################################################################

    def _update_settings(
        self, msg: str | None, **kwargs: Unpack[_SettingsT]
    ) -> None:
        self._set_settings(msg, replace(self.settings, **kwargs))

    ###########################################################################

    def _update_state(
        self, msg: str | None, **kwargs: Unpack[_StateT]
    ) -> None:
        self._set_state(msg, replace(self.state, **kwargs))

    ###########################################################################
    # API property definitions
    ###########################################################################

    @property
    def echo(self) -> EchoConfig:
        return self.settings.echo

    ###########################################################################

    @property
    def info(self) -> ProjectInfo:
        return self.project.info

    ###########################################################################

    @property
    def loaded(self) -> bool:
        return self.state.loaded

    ###########################################################################

    @property
    def project(self) -> Project:
        return self.state.project

    ###########################################################################

    # TODO: This needs to be dependent on a State variable
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
