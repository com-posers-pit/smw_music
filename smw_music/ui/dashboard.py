# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard application."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import enum
from collections import deque
from contextlib import ExitStack, suppress
from functools import cached_property, partial
from os import stat
from pathlib import Path
from typing import Any, Callable, NamedTuple, cast

# Library imports
import qdarkstyle  # type: ignore
from music21.pitch import Pitch
from PyQt6 import uic
from PyQt6.QtCore import QEvent, QModelIndex, QObject, QSignalBlocker, Qt
from PyQt6.QtGui import QAction, QFont, QIcon, QKeyEvent, QMovie, QPixmap
from PyQt6.QtWidgets import (
    QAbstractSlider,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTreeWidgetItem,
    QWidget,
)

# Package imports
from smw_music.common import COPYRIGHT_YEAR, RESOURCES, __version__
from smw_music.ext_tools.amk import (
    N_BUILTIN_SAMPLES,
    BuiltinSampleGroup,
    BuiltinSampleSource,
)
from smw_music.spc700 import Envelope, GainMode
from smw_music.spcmw import EXTENSION, OLD_EXTENSION, Artic
from smw_music.spcmw import Dynamics as Dyn
from smw_music.spcmw import SamplePack, SampleSource, TuneSource
from smw_music.spcmw.project import ProjectInfo, ProjectSettings
from smw_music.utils import brr_size, codename, hexb, pct

from .dashboard_ui import update_sample_opt
from .dashboard_view import DashboardView
from .keyboard import KeyboardEventFilter
from .model import Model
from .preferences import PreferencesDlg
from .project_settings import ProjectSettingsDlg
from .state import NoSample, State
from .utilization import Utilization, paint_utilization, setup_utilization
from .utils import is_checked, to_checkstate

###############################################################################
# Private function definitions
###############################################################################


def _cb_proxy(slot: Callable[[bool], None], state: Qt.CheckState) -> None:
    slot(bool(state))


###############################################################################


def _le_proxy(slot: Callable[[str], None], widget: QLineEdit) -> None:
    slot(widget.text())


###############################################################################


def _mark_unselectable(item: QTreeWidgetItem) -> None:
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)


###############################################################################


# h/t: https://stackoverflow.com/questions/47285303
def _set_lineedit_width(edit: QLineEdit, limit: str = "1000.0%") -> None:
    fontmetrics = edit.fontMetrics()
    tmargins = edit.textMargins()
    cmargins = edit.contentsMargins()
    edit.setFixedWidth(
        fontmetrics.boundingRect(limit).width()
        + tmargins.left()
        + tmargins.right()
        + cmargins.left()
        + cmargins.right()
    )


###############################################################################


def _slider_inv(slider: QSlider, val: int) -> int:
    return slider.maximum() - val


###############################################################################
# Private constant definitions
###############################################################################

_KONAMI = deque(
    [
        Qt.Key.Key_Up,
        Qt.Key.Key_Up,
        Qt.Key.Key_Down,
        Qt.Key.Key_Down,
        Qt.Key.Key_Left,
        Qt.Key.Key_Right,
        Qt.Key.Key_Left,
        Qt.Key.Key_Right,
        Qt.Key.Key_B,
        Qt.Key.Key_A,
    ]
)

###############################################################################

_REV_KONAMI = deque(reversed(_KONAMI))

###############################################################################
# Private class definitions
###############################################################################


class _ArticWidgets(NamedTuple):
    length_slider: QSlider
    length_setting: QLineEdit
    volume_slider: QSlider
    volume_setting: QLineEdit
    setting_label: QLabel


###############################################################################


class _DynamicsWidgets(NamedTuple):
    slider: QSlider
    setting: QLineEdit
    label: QLabel


###############################################################################


class _SampleRemover(QObject):
    def __init__(self, model: Model) -> None:
        super().__init__()
        self._model = model

    ###########################################################################

    def eventFilter(self, _: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyRelease:
            if cast(QKeyEvent, event).key() == Qt.Key.Key_Delete:
                self._model.on_multisample_sample_remove_clicked()
                return True
        return False


###############################################################################


class _TblCol(enum.IntEnum):
    NAME = 0
    SOLO = 1
    MUTE = 2


###############################################################################
# API class definitions
###############################################################################


class Dashboard(QWidget):
    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self, prj_file: Path | None = None) -> None:
        super().__init__()

        self._window_title = f"SPaCeMusicW v{__version__}"

        self._keyhist: deque[int] = deque(maxlen=len(_KONAMI))
        ui_contents = RESOURCES / "dashboard.ui"

        self._view: DashboardView = uic.loadUi(ui_contents)
        self._view.installEventFilter(self)
        self._view.setWindowTitle(self._window_title)

        self._preferences = PreferencesDlg()
        self._project_settings = ProjectSettingsDlg()
        self._model = Model()
        self._sample_pack_items: dict[tuple[str, Path], QTreeWidgetItem] = {}
        self._samples: dict[tuple[str, str | None], QTreeWidgetItem] = {}

        self._confirm_render = True

        # h/t: https://forum.qt.io/topic/35999
        font = QFont("_")
        font.setStyleHint(QFont.StyleHint.Monospace)
        self._view.mml_view.setFont(font)

        self._checkitout = QMainWindow(parent=self)
        self._checkitout.setWindowTitle(
            "Never gonna run around and desert you"
        )
        label = QLabel(self)
        movie = QMovie(parent=self)
        movie.setFileName(str(RESOURCES / "ashtley.gif"))
        label.setMovie(movie)
        movie.start()
        self._checkitout.setCentralWidget(label)

        self._camelitout = QMainWindow(parent=self)
        self._camelitout.setWindowTitle("Camel by camel")
        label = QLabel(self)
        movie = QMovie(parent=self)
        movie.setFileName(str(RESOURCES / "ankha.gif"))
        label.setMovie(movie)
        movie.start()
        self._camelitout.setCentralWidget(label)

        self._setup_menus()
        self._fix_edit_widths()
        self._combine_widgets()
        self._setup_instrument_table()
        self._attach_signals()

        self._default_tooltips = {
            widget: widget.toolTip() for widget in self._view_widgets
        }

        for widget in [
            self._view,
            self._checkitout,
        ]:
            widget.setWindowIcon(QIcon(str(RESOURCES / "maestro.svg")))

        self._sample_remover = _SampleRemover(self._model)
        self._view.sample_list.installEventFilter(self._sample_remover)

        self._kbd_filter = KeyboardEventFilter(self._view.audition_player)
        # QApplication.instance().installEventFilter(self._kbd_filter)

        self._view.show()

        self._model.start()

        if prj_file is not None:
            self._model.on_load(prj_file)

    ###########################################################################
    # API slot definitions
    ###########################################################################

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        match event.type():
            case QEvent.Type.Close:
                reply = self._prompt_to_save()

                if reply is None:
                    quit_msg = "Close program?"
                    reply = QMessageBox.question(
                        self._view,
                        "Close program",
                        quit_msg,
                        QMessageBox.StandardButton.Yes
                        | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No,
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        event.accept()
                    else:
                        event.ignore()
                else:
                    if reply == QMessageBox.StandardButton.Cancel:
                        event.ignore()
                    else:
                        event.accept()
                return True
            case QEvent.Type.KeyRelease:
                self._keyhist.append(cast(QKeyEvent, event).key())
                if self._keyhist == _KONAMI:
                    self._checkitout.show()
                elif self._keyhist == _REV_KONAMI:
                    self._camelitout.show()

        return False

    ###########################################################################
    # API slot definitions
    ###########################################################################

    def on_brr_clicked(self) -> None:
        fname, _ = QFileDialog.getOpenFileName(
            self._view, caption="BRR Sample File", filter="BRR Files (*.brr)"
        )
        if fname:
            self._model.on_brr_fname_changed(fname)

    ###########################################################################

    def on_mml_generated(self, mml: str) -> None:
        self._view.mml_view.setText(mml)

    ###########################################################################

    def on_multisample_sample_add_clicked(self) -> None:
        v = self._view

        self._model.on_multisample_sample_add_clicked(
            v.multisample_sample_name.text(),
            v.multisample_sample_notes.text(),
            v.multisample_sample_notehead.currentText(),
            v.multisample_sample_output.text(),
            is_checked(v.multisample_sample_track),
        )

    ###########################################################################

    def on_multisample_sample_changed(self, _: Any) -> None:
        v = self._view

        self._model.on_multisample_sample_changed(
            v.multisample_sample_name.text(),
            v.multisample_sample_notes.text(),
            v.multisample_sample_notehead.currentText(),
            v.multisample_sample_output.text(),
            is_checked(v.multisample_sample_track),
        )

    ###########################################################################

    def on_pack_sample_changed(self) -> None:
        items = self._view.sample_pack_list.selectedItems()
        if items:
            self._model.on_pack_sample_changed(
                items[0].data(0, Qt.ItemDataRole.UserRole)
            )

    ###########################################################################

    def on_preferences_changed(
        self,
        advanced_enabled: bool,
        amk_valid: bool,
        spcplayer_valid: bool,
        dark_mode: bool,
    ) -> None:
        v = self._view

        sheet = qdarkstyle.load_stylesheet(qt_api="pyqt6") if dark_mode else ""
        cast(QApplication, QApplication.instance()).setStyleSheet(sheet)
        self._setup_utilization(dark_mode)

        # advance_enabled handling
        v.generate_mml.setVisible(advanced_enabled)
        v.generate_spc.setVisible(advanced_enabled)
        v.play_spc.setVisible(advanced_enabled)
        v.other_settings_box.setVisible(advanced_enabled)
        v.tuning_use_auto_freq.setVisible(advanced_enabled)
        v.tuning_use_manual_note.setVisible(advanced_enabled)
        v.tuning_manual_note_label.setVisible(advanced_enabled)
        v.tuning_manual_note.setVisible(advanced_enabled)
        v.tuning_manual_octave.setVisible(advanced_enabled)
        v.tuning_use_manual_freq.setVisible(advanced_enabled)
        v.tuning_manual_freq_label.setVisible(advanced_enabled)
        v.tuning_manual_freq.setVisible(advanced_enabled)
        v.tuning_sample_freq_label.setVisible(advanced_enabled)
        v.tuning_sample_freq.setVisible(advanced_enabled)
        v.tuning_output_note.setVisible(advanced_enabled)
        v.tuning_output_note_label.setText(
            "Note" if advanced_enabled else "Octave"
        )

        # amk_valid handling
        enable = amk_valid and spcplayer_valid
        widgets: list[QAction | QMenu] = [
            v.new_project,
            v.open_project,
            v.save_project,
            v.menuRecent_Projects,
        ]
        for action in widgets:
            tooltip = (
                "Define AMK zip file and spcplayer executable in "
                "preferences to enable this"
            )

            if enable:
                tooltip = self._default_tooltips[action]

            action.setToolTip(tooltip)
            action.setEnabled(enable)

    ###########################################################################

    def on_recent_projects_updated(self, projects: list[Path]) -> None:
        menu = self._view.menuRecent_Projects
        clear = self._view.actionClearRecentProjects
        menu.clear()

        menu.addAction(clear)
        last_action = menu.insertSeparator(clear)

        for n, project in enumerate(projects):
            action = QAction(parent=menu)
            action.setText(f"{len(projects) - n} | {str(project)}")
            action.triggered.connect(partial(self._model.on_load, project))
            menu.insertAction(last_action, action)
            last_action = action

    ###########################################################################

    def on_response_generated(
        self, error: bool, title: str, results: str
    ) -> None:
        if error:
            QMessageBox.critical(self._view, title, results)
        else:
            QMessageBox.information(self._view, title, results)

    ###########################################################################

    def on_sample_packs_changed(
        self, sample_packs: dict[str, SamplePack]
    ) -> None:
        # sample_packs handling
        self._sample_pack_items = {}
        tree = self._view.sample_pack_list

        tree.clear()

        for name, pack in sample_packs.items():
            top = QTreeWidgetItem(tree, [name])
            _mark_unselectable(top)

            self._add_sample_pack(top, name, pack)
            tree.addTopLevelItem(top)

        tree.resizeColumnToContents(0)
        tree.resizeColumnToContents(1)

    ###########################################################################

    def on_song_loaded(self, loaded: bool) -> None:
        widgets: set[QWidget | QAction] = set(
            x
            for x in self._view_widgets
            if not isinstance(x, (QMenu, QMenuBar, QAction))
        )
        v = self._view
        widgets |= set(
            [
                v.save_project,
                v.close_project,
                v.open_project_settings,
                v.undo,
                v.redo,
            ]
        )

        for child in widgets:
            with QSignalBlocker(child):
                child.setEnabled(loaded)

    ###########################################################################

    def on_songinfo_changed(self, msg: str) -> None:
        self._view.song_info_view.setText(msg)

    ###########################################################################

    def on_state_changed(self, update_instruments: bool) -> None:
        state = self._state
        settings = self._proj_settings

        if update_instruments:
            self._update_instruments(state)

        v = self._view

        title = "[No project]"
        if self._loaded:
            title = f"[{self._proj_info.project_name}]"
            if self._unsaved:
                title += " +"

        title += f" - {self._window_title}"
        v.setWindowTitle(title)

        self._utilization_updated(state.aram_util)

        with ExitStack() as stack:
            for child in self._view_widgets:
                stack.enter_context(QSignalBlocker(child))

            v.loop_analysis.setChecked(settings.loop_analysis)
            v.superloop_analysis.setChecked(settings.superloop_analysis)
            v.measure_numbers.setChecked(settings.measure_numbers)
            v.start_measure.setValue(state.start_measure)

            # Solo/mute settings
            sample_list = self._view.sample_list
            sample_list.clearSelection()
            with suppress(NoSample):
                sample_idx = state.sample_idx
                sample_list.setCurrentItem(
                    self._samples[sample_idx], _TblCol.NAME
                )
                self._update_sample_config(state, sample_idx)

            self._update_solomute(state)
            self._update_multisample(state)

            with suppress(NoSample):
                if state.sample.sample_source == SampleSource.BUILTIN:
                    v.sample_pack_list.clearSelection()
                tuning = state.sample.tuning
                v.tuning_use_auto_freq.setChecked(
                    tuning.source == TuneSource.AUTO
                )
                v.tuning_use_manual_freq.setChecked(
                    tuning.source == TuneSource.MANUAL_FREQ
                )
                v.tuning_use_manual_note.setChecked(
                    tuning.source == TuneSource.MANUAL_NOTE
                )
                v.tuning_semitone_shift.setValue(tuning.semitone_shift)
                v.tuning_manual_note.setCurrentIndex(tuning.pitch.pitchClass)
                v.tuning_manual_octave.setValue(tuning.pitch.implicitOctave)
                v.tuning_manual_freq.setText(f"{tuning.frequency:.2f}")
                v.tuning_sample_freq.setText(f"{tuning.sample_freq:.2f}")

                freq, (setting, actual) = state.calculated_tune
                v.tuning_auto_freq.setText(f"{freq:.2f}Hz")
                freq = tuning.output.frequency
                v.tuning_goal_freq.setText(f"{freq:.2f}Hz")
                tune, subtune = divmod(setting, 256)
                v.tuning_recommended_pitch.setText(f"{actual:.2f}Hz")
                v.tuning_recommendation.setText(f"${tune:02x} ${subtune:02x}")

            # Global settings
            v.global_volume_slider.setValue(settings.global_volume)
            v.global_volume_setting.setText(pct(settings.global_volume))
            v.global_volume_setting_label.setText(hexb(settings.global_volume))
            v.global_legato.setChecked(settings.global_legato)

            v.echo_enable.setChecked(settings.global_echo)
            v.echo_filter_0.setChecked(settings.echo.fir_filt == 0)
            v.echo_filter_1.setChecked(settings.echo.fir_filt == 1)

            v.echo_left_slider.setValue(
                int(v.echo_left_slider.maximum() * settings.echo.vol_mag[0])
            )
            v.echo_left_setting.setText(pct(settings.echo.vol_mag[0], 1.0))
            v.echo_left_surround.setChecked(settings.echo.vol_inv[0])
            v.echo_left_setting_label.setText(hexb(settings.echo.left_vol_reg))
            v.echo_right_slider.setValue(
                int(v.echo_right_slider.maximum() * settings.echo.vol_mag[1])
            )
            v.echo_right_setting.setText(pct(settings.echo.vol_mag[1], 1.0))
            v.echo_right_surround.setChecked(settings.echo.vol_inv[1])
            v.echo_right_setting_label.setText(
                hexb(settings.echo.right_vol_reg)
            )
            v.echo_feedback_slider.setValue(
                int(v.echo_feedback_slider.maximum() * settings.echo.fb_mag)
            )
            v.echo_feedback_setting.setText(pct(settings.echo.fb_mag, 1.0))
            v.echo_feedback_surround.setChecked(settings.echo.fb_inv)
            v.echo_feedback_setting_label.setText(hexb(settings.echo.fb_reg))
            v.echo_delay_slider.setValue(settings.echo.delay)
            v.echo_delay_setting.setText(hexb(settings.echo.delay))
            v.echo_delay_setting_label.setText(f"{16*settings.echo.delay}ms")

            for widget in self._echo_widgets:
                widget.setEnabled(settings.global_echo)

            v.start_section.setSizeAdjustPolicy(
                QComboBox.SizeAdjustPolicy.AdjustToContents
            )

            v.start_section.clear()
            v.start_section.addItems(state.section_names)
            v.start_section.setCurrentIndex(state.start_section_idx)

            update_sample_opt(v, state)

    ###########################################################################

    def on_status_updated(self, msg: str) -> None:
        self._view.history_view.insertItem(0, msg)
        self._view.statusBar().showMessage(msg)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _about(self) -> None:
        title = "About MusicXML -> MML"
        text = f"Version: {__version__} ({codename()})"
        text += f"\nCopyright Ⓒ {COPYRIGHT_YEAR} The SMW Music Python Project "
        text += "Authors"
        text += "\nHomepage: https://github.com/com-posers-pit/smw_music"

        QMessageBox.about(self._view, title, text)

    ###########################################################################

    def _add_sample_pack(
        self, top: QTreeWidgetItem, name: str, pack: SamplePack
    ) -> None:
        parent = top
        parent_items: dict[Path, QTreeWidgetItem] = {}

        for sample in pack.samples:
            parent_paths = sample.path.parents

            for path in reversed(parent_paths[:-1]):
                try:
                    parent = parent_items[path]
                except KeyError:
                    item = QTreeWidgetItem(parent, [path.name])
                    _mark_unselectable(item)
                    parent_items[path] = item
                    parent = item

            item = QTreeWidgetItem(
                parent, [sample.path.name, brr_size(len(sample.data))]
            )
            item_id = (name, sample.path)
            item.setData(0, Qt.ItemDataRole.UserRole, item_id)
            self._sample_pack_items[item_id] = item

    ###########################################################################

    def _attach_signals(self) -> None:  # pylint: disable=too-many-statements
        m = self._model
        v = self._view

        # Short aliases to avoid line wrapping
        alen = m.on_artic_length_changed
        avol = m.on_artic_volume_changed

        connections: list[tuple[QWidget, Callable[..., None]]] = [
            # Control Panel
            (v.loop_analysis, m.on_loop_analysis_changed),
            (v.superloop_analysis, m.on_superloop_analysis_changed),
            (v.measure_numbers, m.on_measure_numbers_changed),
            (v.start_measure, m.on_start_measure_changed),
            (v.generate_mml, m.on_generate_mml_clicked),
            (v.generate_spc, m.on_generate_spc_clicked),
            (v.play_spc, m.on_play_spc_clicked),
            (v.generate_and_play, m.on_generate_and_play_clicked),
            (v.reload_musicxml, m.on_reload_musicxml_clicked),
            (v.render_zip, self._on_render_zip_clicked),
            # Instrument settings
            (v.interpolate, m.on_interpolate_changed),
            # Instrument pan settings
            (v.pan_enable, m.on_pan_enable_changed),
            (v.pan_setting, m.on_pan_setting_changed),
            (v.pan_l_invert, partial(m.on_pan_invert_changed, True)),
            (v.pan_r_invert, partial(m.on_pan_invert_changed, False)),
            (v.multisample_sample_add, self.on_multisample_sample_add_clicked),
            (
                v.multisample_sample_remove,
                m.on_multisample_sample_remove_clicked,
            ),
            (v.multisample_sample_name, self.on_multisample_sample_changed),
            (v.multisample_sample_notes, self.on_multisample_sample_changed),
            (
                v.multisample_sample_notehead,
                self.on_multisample_sample_changed,
            ),
            (v.multisample_sample_output, self.on_multisample_sample_changed),
            (v.multisample_sample_track, self.on_multisample_sample_changed),
            # Instrument sample
            (v.select_builtin_sample, m.on_builtin_sample_selected),
            (v.builtin_sample, m.on_builtin_sample_changed),
            (v.select_pack_sample, m.on_pack_sample_selected),
            (v.select_brr_sample, m.on_brr_sample_selected),
            (v.select_brr_fname, self.on_brr_clicked),
            (v.select_multisample_sample, m.on_multisample_sample_selected),
            (v.brr_fname, m.on_brr_fname_changed),
            (v.octave_shift, m.on_octave_shift_changed),
            (v.select_adsr_mode, m.on_select_adsr_mode_selected),
            (v.gain_mode_direct, m.on_gain_direct_selected),
            (v.gain_mode_inclin, m.on_gain_inclin_selected),
            (v.gain_mode_incbent, m.on_gain_incbent_selected),
            (v.gain_mode_declin, m.on_gain_declin_selected),
            (v.gain_mode_decexp, m.on_gain_decexp_selected),
            (v.gain_slider, m.on_gain_changed),
            (v.gain_setting, m.on_gain_changed),
            (
                v.attack_slider,
                lambda x: m.on_attack_changed(_slider_inv(v.attack_slider, x)),
            ),
            (v.attack_setting, m.on_attack_changed),
            (
                v.decay_slider,
                lambda x: m.on_decay_changed(_slider_inv(v.decay_slider, x)),
            ),
            (v.decay_setting, m.on_decay_changed),
            (v.sus_level_slider, m.on_sus_level_changed),
            (v.sus_level_setting, m.on_sus_level_changed),
            (
                v.sus_rate_slider,
                lambda x: m.on_sus_rate_changed(
                    _slider_inv(v.sus_rate_slider, x)
                ),
            ),
            (v.sus_rate_setting, m.on_sus_rate_changed),
            (v.tuning_use_auto_freq, m.on_tuning_use_auto_freq_selected),
            (v.tuning_use_manual_freq, m.on_tuning_use_manual_freq_selected),
            (v.tuning_use_manual_note, m.on_tuning_use_manual_note_selected),
            (v.tuning_semitone_shift, m.on_tuning_semitone_shift_changed),
            (v.tuning_manual_freq, m.on_tuning_manual_freq_changed),
            (v.tuning_manual_note, self._on_tuning_manual_note_changed),
            (v.tuning_manual_octave, self._on_tuning_manual_octave_changed),
            (v.tuning_sample_freq, m.on_tuning_sample_freq_changed),
            (v.tuning_output_note, self._on_tuning_output_note_changed),
            (v.tuning_output_octave, self._on_tuning_output_octave_changed),
            (v.apply_suggested_tune, m.on_apply_suggested_tune_clicked),
            (v.tune_slider, m.on_tune_changed),
            (v.tune_setting, m.on_tune_changed),
            (v.subtune_slider, m.on_subtune_changed),
            (v.subtune_setting, m.on_subtune_changed),
            (v.brr_setting, m.on_brr_setting_changed),
            # Global settings
            (v.global_volume_slider, m.on_global_volume_changed),
            (v.global_volume_setting, m.on_global_volume_changed),
            (v.global_legato, m.on_global_legato_changed),
            (v.echo_enable, m.on_global_echo_en_changed),
            (v.echo_filter_0, m.on_filter_0_toggled),
            (v.echo_left_slider, m.on_echo_left_changed),
            (v.echo_left_setting, m.on_echo_left_changed),
            (v.echo_left_surround, m.on_echo_left_surround_changed),
            (v.echo_right_slider, m.on_echo_right_changed),
            (v.echo_right_setting, m.on_echo_right_changed),
            (v.echo_right_surround, m.on_echo_right_surround_changed),
            (v.echo_feedback_slider, m.on_echo_feedback_changed),
            (v.echo_feedback_setting, m.on_echo_feedback_changed),
            (v.echo_feedback_surround, m.on_echo_feedback_surround_changed),
            (v.echo_delay_slider, m.on_echo_delay_changed),
            (v.echo_delay_setting, m.on_echo_delay_changed),
            # Builtin sample selection
            (
                v.sample_opt_default,
                partial(m.on_sample_opt_selected, BuiltinSampleGroup.DEFAULT),
            ),
            (
                v.sample_opt_optimized,
                partial(
                    m.on_sample_opt_selected, BuiltinSampleGroup.OPTIMIZED
                ),
            ),
            (
                v.sample_opt_redux1,
                partial(m.on_sample_opt_selected, BuiltinSampleGroup.REDUX1),
            ),
            (
                v.sample_opt_redux2,
                partial(m.on_sample_opt_selected, BuiltinSampleGroup.REDUX2),
            ),
            (
                v.sample_opt_custom,
                partial(m.on_sample_opt_selected, BuiltinSampleGroup.CUSTOM),
            ),
        ]

        for n in range(N_BUILTIN_SAMPLES):
            w = getattr(v, f"sample_opt_{n:02x}")
            connections.append(
                (w, partial(self._on_sample_opt_source_changed, n))
            )

        # Instrument dynamics settings
        for dkey, dwidgets in self._dyn_widgets.items():
            dyn_slot = partial(m.on_dynamics_changed, dkey)
            connections.append((dwidgets.slider, dyn_slot))
            connections.append((dwidgets.setting, dyn_slot))

        # Instrument articulation settings
        for akey, awidgets in self._artic_widgets.items():
            alen_slot = partial(alen, akey)
            avol_slot = partial(avol, akey)
            connections.append((awidgets.length_slider, alen_slot))
            connections.append((awidgets.length_setting, alen_slot))
            connections.append((awidgets.volume_slider, avol_slot))
            connections.append((awidgets.volume_setting, avol_slot))

        for widget, slot in connections:
            if isinstance(widget, QPushButton):
                widget.released.connect(slot)
            elif isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(slot)
            elif isinstance(widget, QCheckBox):
                widget.stateChanged.connect(partial(_cb_proxy, slot))
            elif isinstance(widget, QLineEdit):
                widget.editingFinished.connect(
                    partial(_le_proxy, slot, widget)
                )
            elif isinstance(widget, QRadioButton):
                widget.toggled.connect(slot)
            elif isinstance(widget, (QAbstractSlider, QSpinBox)):
                widget.valueChanged.connect(slot)
            else:
                # This is basically a compile-time exception
                raise Exception(f"Unhandled widget connection {widget}")

        v.sample_list.itemChanged.connect(self._on_solomute_change)
        v.sample_list.itemSelectionChanged.connect(self._on_sample_change)
        v.sample_pack_list.itemSelectionChanged.connect(
            self.on_pack_sample_changed
        )

        v.multisample_unmapped_list.doubleClicked.connect(
            self._on_multisample_unmapped_doubleclicked
        )

        v.start_section.activated.connect(m.on_start_section_activated)

        v.audition_player.key_on.connect(self._on_audition_start)
        v.audition_player.key_off.connect(lambda x, y: m.on_audition_stop())

        # Return signals
        m.state_changed.connect(self.on_state_changed)
        m.mml_generated.connect(self.on_mml_generated)
        m.response_generated.connect(self.on_response_generated)
        m.preferences_changed.connect(self.on_preferences_changed)
        m.sample_packs_changed.connect(self.on_sample_packs_changed)
        m.recent_projects_updated.connect(self.on_recent_projects_updated)
        v.actionClearRecentProjects.triggered.connect(
            m.on_recent_projects_cleared
        )
        m.status_updated.connect(self.on_status_updated)
        m.songinfo_changed.connect(self.on_songinfo_changed)
        m.song_loaded.connect(self.on_song_loaded)

    ###########################################################################

    def _combine_widgets(self) -> None:
        v = self._view
        self._dyn_widgets: dict[Dyn, _DynamicsWidgets] = {}
        dyns = self._dyn_widgets
        dyns[Dyn.PPPP] = _DynamicsWidgets(
            v.pppp_slider, v.pppp_setting, v.pppp_setting_label
        )
        dyns[Dyn.PPP] = _DynamicsWidgets(
            v.ppp_slider, v.ppp_setting, v.ppp_setting_label
        )
        dyns[Dyn.PP] = _DynamicsWidgets(
            v.pp_slider, v.pp_setting, v.pp_setting_label
        )
        dyns[Dyn.P] = _DynamicsWidgets(
            v.p_slider, v.p_setting, v.p_setting_label
        )
        dyns[Dyn.MP] = _DynamicsWidgets(
            v.mp_slider, v.mp_setting, v.mp_setting_label
        )
        dyns[Dyn.MF] = _DynamicsWidgets(
            v.mf_slider, v.mf_setting, v.mf_setting_label
        )
        dyns[Dyn.F] = _DynamicsWidgets(
            v.f_slider, v.f_setting, v.f_setting_label
        )
        dyns[Dyn.FF] = _DynamicsWidgets(
            v.ff_slider, v.ff_setting, v.ff_setting_label
        )
        dyns[Dyn.FFF] = _DynamicsWidgets(
            v.fff_slider, v.fff_setting, v.fff_setting_label
        )
        dyns[Dyn.FFFF] = _DynamicsWidgets(
            v.ffff_slider, v.ffff_setting, v.ffff_setting_label
        )

        self._artic_widgets = {}
        self._artic_widgets[Artic.ACC] = _ArticWidgets(
            v.artic_acc_length_slider,
            v.artic_acc_length_setting,
            v.artic_acc_volume_slider,
            v.artic_acc_volume_setting,
            v.artic_acc_setting_label,
        )
        self._artic_widgets[Artic.DEF] = _ArticWidgets(
            v.artic_default_length_slider,
            v.artic_default_length_setting,
            v.artic_default_volume_slider,
            v.artic_default_volume_setting,
            v.artic_default_setting_label,
        )
        self._artic_widgets[Artic.STAC] = _ArticWidgets(
            v.artic_stacc_length_slider,
            v.artic_stacc_length_setting,
            v.artic_stacc_volume_slider,
            v.artic_stacc_volume_setting,
            v.artic_stacc_setting_label,
        )
        self._artic_widgets[Artic.ACCSTAC] = _ArticWidgets(
            v.artic_accstacc_length_slider,
            v.artic_accstacc_length_setting,
            v.artic_accstacc_volume_slider,
            v.artic_accstacc_volume_setting,
            v.artic_accstacc_setting_label,
        )

    ###########################################################################

    def _create_project(self) -> None:
        proj_dir, _ = QFileDialog.getSaveFileName(self._view, "Project")
        if proj_dir:
            proj_dir = Path(proj_dir)
            info = self._update_project_settings(
                ProjectInfo(proj_dir, proj_dir.name)
            )
            if info is not None:
                # Directly execute this so future calls block until completion
                self._model.create_project(info)

    ###########################################################################

    def _fix_edit_widths(self) -> None:
        v = self._view
        widgets: list[QLineEdit] = [
            v.pppp_setting,
            v.ppp_setting,
            v.pp_setting,
            v.p_setting,
            v.mp_setting,
            v.mf_setting,
            v.f_setting,
            v.ff_setting,
            v.fff_setting,
            v.ffff_setting,
            v.artic_default_length_setting,
            v.artic_default_volume_setting,
            v.artic_acc_length_setting,
            v.artic_acc_volume_setting,
            v.artic_stacc_length_setting,
            v.artic_stacc_volume_setting,
            v.artic_accstacc_length_setting,
            v.artic_accstacc_volume_setting,
            v.attack_setting,
            v.decay_setting,
            v.sus_level_setting,
            v.sus_rate_setting,
            v.gain_setting,
            v.tune_setting,
            v.subtune_setting,
            v.global_volume_setting,
            v.echo_left_setting,
            v.echo_right_setting,
            v.echo_feedback_setting,
            v.echo_delay_setting,
        ]

        for widget in widgets:
            _set_lineedit_width(widget)

        _set_lineedit_width(v.brr_setting, " ".join(5 * hexb(0)))

    ###########################################################################

    def _make_sample_item(
        self, name: str, role: tuple[str, str]
    ) -> QTreeWidgetItem:
        item = QTreeWidgetItem([name])
        item.setToolTip(_TblCol.SOLO, f"Solo {name}")
        item.setToolTip(_TblCol.MUTE, f"Mute {name}")

        item.setCheckState(_TblCol.SOLO, Qt.CheckState.Unchecked)
        item.setCheckState(_TblCol.MUTE, Qt.CheckState.Unchecked)

        self._samples[role] = item
        item.setData(_TblCol.NAME, Qt.ItemDataRole.UserRole, role)

        return item

    ###########################################################################

    def _on_audition_start(self, note: str, octave: int) -> None:
        self._model.on_audition_start(f"{note}{octave}")

    ###########################################################################

    def _on_close_project_clicked(self) -> None:
        close = self._prompt_to_save()
        if close != QMessageBox.StandardButton.Cancel:
            self._model.close_project()

    ###########################################################################

    def _on_multisample_unmapped_doubleclicked(self, idx: QModelIndex) -> None:
        v = self._view
        item = v.multisample_unmapped_list.itemFromIndex(idx)

        name = f"TMP{self._view.multisample_unmapped_list.count()}_"
        note, notehead = cast(
            tuple[Pitch, str], item.data(Qt.ItemDataRole.UserRole)
        )

        self._model.on_multisample_sample_add_clicked(
            name,
            str(note),
            notehead,
            note.nameWithOctave,
            is_checked(v.multisample_sample_track),
        )

    ###########################################################################

    def _on_open_project_settings(self) -> None:
        info = self._update_project_settings(self._proj_info)
        if info is not None:
            # TODO: Update project info
            pass

    ###########################################################################

    def _on_render_zip_clicked(self) -> None:
        do_render = True
        if self._confirm_render:
            do_render = QMessageBox.StandardButton.Yes == QMessageBox.question(
                self._view,
                "Render",
                "Generate a zip for upload?",
            )

        if do_render:
            self._model.on_render_zip_clicked()

    ###########################################################################

    def _on_sample_change(self) -> None:
        widget = self._view.sample_list
        sample = widget.currentItem().data(
            _TblCol.NAME, Qt.ItemDataRole.UserRole
        )
        self._model.on_sample_changed(sample)

    ###########################################################################

    def _on_sample_opt_source_changed(self, n: int, idx: int) -> None:
        src = [
            BuiltinSampleSource.DEFAULT,
            BuiltinSampleSource.OPTIMIZED,
            BuiltinSampleSource.EMPTY,
        ]
        self._model.on_sample_opt_source_changed(n, src[idx])

    ###########################################################################

    def _on_solomute_change(self, item: QTreeWidgetItem, col: int) -> None:
        checked = item.checkState(col) == Qt.CheckState.Checked
        sample = item.data(_TblCol.NAME, Qt.ItemDataRole.UserRole)

        solo = col == _TblCol.SOLO
        self._model.on_solomute_changed(sample, solo, checked)

    ###########################################################################

    def _on_tuning_manual_note_changed(self, pitch_class: int) -> None:
        octave = self._view.tuning_manual_octave.value()
        self._model.on_tuning_manual_note_changed(pitch_class, octave)

    ###########################################################################

    def _on_tuning_manual_octave_changed(self, octave: int) -> None:
        pitch_class = self._view.tuning_manual_note.currentIndex()
        self._model.on_tuning_manual_note_changed(pitch_class, octave)

    ###########################################################################

    def _on_tuning_output_note_changed(self, pitch_class: int) -> None:
        octave = self._view.tuning_output_octave.value()
        self._model.on_tuning_output_note_changed(pitch_class, octave)

    ###########################################################################

    def _on_tuning_output_octave_changed(self, octave: int) -> None:
        pitch_class = self._view.tuning_output_note.currentIndex()
        self._model.on_tuning_output_note_changed(pitch_class, octave)

    ###########################################################################

    def _open_project(self) -> None:
        exts = f"*.{EXTENSION} *.{OLD_EXTENSION}"
        fname, _ = QFileDialog.getOpenFileName(
            self._view, "Project File", filter=f"SPCMW Project Files ({exts})"
        )
        if fname:
            self._model.on_load(Path(fname))

    ###########################################################################

    def _open_preferences(self) -> None:
        preferences = self._preferences.exec(self._model.preferences)
        if preferences:
            self._model.update_preferences(preferences)

    ###########################################################################

    def _prompt_to_save(self) -> QMessageBox.StandardButton | None:
        reply = None
        if self._loaded and self._unsaved:
            quit_msg = "Save project before closing?"
            std = QMessageBox.StandardButton
            reply = QMessageBox.question(
                self._view,
                "Save project",
                quit_msg,
                std.Yes | std.No | std.Cancel,
                std.Cancel,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._model.on_save()
        return reply

    ###########################################################################

    def _setup_instrument_table(self) -> None:
        widget = self._view.sample_list
        widget.header().moveSection(_TblCol.NAME, len(_TblCol) - 1)

        for n in _TblCol:
            widget.resizeColumnToContents(n)

    ###########################################################################

    def _setup_menus(self) -> None:
        view = self._view
        model = self._model

        view.new_project.triggered.connect(self._create_project)
        view.open_project.triggered.connect(self._open_project)
        view.save_project.triggered.connect(model.on_save)
        view.close_project.triggered.connect(self._on_close_project_clicked)
        view.open_project_settings.triggered.connect(
            self._on_open_project_settings
        )
        view.exit_dashboard.triggered.connect(QApplication.quit)

        view.undo.triggered.connect(model.on_undo_clicked)
        view.redo.triggered.connect(model.on_redo_clicked)
        view.open_preferences.triggered.connect(self._open_preferences)

        view.show_about.triggered.connect(self._about)
        view.show_about_qt.triggered.connect(QApplication.aboutQt)

    ###########################################################################

    def _setup_utilization(self, dark: bool) -> None:
        v = self._view
        util = v.utilization

        canvas = QPixmap(util.width(), util.height())
        canvas.fill(Qt.GlobalColor.black)
        util.setPixmap(canvas)

        setup_utilization(
            dark,
            v.utilization_engine,
            v.utilization_song,
            v.utilization_samples,
            v.utilization_echo,
        )

    ###########################################################################

    def _update_envelope(self, env: Envelope) -> None:
        view = self._view
        prev = self._view.envelope_preview

        if env.adsr_mode:
            labels = prev.plot_adsr(
                env.attack_setting,
                env.decay_setting,
                env.sus_level_setting,
                env.sus_rate_setting,
            )
            view.attack_eu_label.setText(labels[0])
            view.decay_eu_label.setText(labels[1])
            view.sus_level_eu_label.setText(labels[2])
            view.sus_rate_eu_label.setText(labels[3])
        else:  # gain mode
            match env.gain_mode:
                case GainMode.DIRECT:
                    label = prev.plot_direct_gain(env.gain_setting)
                case GainMode.INCLIN:
                    label = prev.plot_inclin(env.gain_setting)
                case GainMode.INCBENT:
                    label = prev.plot_incbent(env.gain_setting)
                case GainMode.DECLIN:
                    label = prev.plot_declin(env.gain_setting)
                case GainMode.DECEXP:
                    label = prev.plot_decexp(env.gain_setting)
                case _:
                    label = ""
            view.gain_eu_label.setText(label)

    ###########################################################################

    def _update_gain_limits(self, direct_mode: bool) -> None:
        view = self._view
        if direct_mode:
            view.gain_slider.setMaximum(127)
        else:
            val = min(31, view.gain_slider.value())
            view.gain_slider.setValue(val)
            view.gain_slider.setMaximum(31)

    ###########################################################################

    def _update_instruments(self, state: State) -> None:
        widget = self._view.sample_list

        open_inst = None
        with suppress(NoSample):
            open_inst = state.sample_idx[0]

        with QSignalBlocker(widget):
            widget.clear()
            self._samples.clear()

            for inst_name, inst in state.project.settings.instruments.items():
                parent = self._make_sample_item(inst_name, (inst_name, ""))
                widget.addTopLevelItem(parent)

                for sample_name in sorted(inst.multisamples.keys()):
                    item = self._make_sample_item(
                        sample_name, (inst_name, sample_name)
                    )
                    parent.addChild(item)

                if inst_name == open_inst:
                    widget.expand(widget.indexFromItem(parent))

        for n in _TblCol:
            widget.resizeColumnToContents(n)

    ###########################################################################

    def _update_multisample(self, state: State) -> None:
        v = self._view
        name = ""
        notes = ""
        notehead = "normal"
        start = ""
        track = False
        with suppress(NoSample):
            sample = state.sample
            name = state.sample_idx[1]

            if name:
                notehead = sample.notehead.symbol
                if sample.llim == sample.ulim:
                    notes = sample.llim.nameWithOctave
                else:
                    notes = ":".join(
                        x.nameWithOctave for x in [sample.llim, sample.ulim]
                    )
                start = sample.start.nameWithOctave
                track = sample.track

        v.multisample_sample_name.setText(name)
        v.multisample_sample_notehead.setCurrentText(notehead)
        v.multisample_sample_notes.setText(notes)
        v.multisample_sample_output.setText(start)
        v.multisample_sample_track.setChecked(track)

        self._update_unmapped(state)

    ###########################################################################

    def _update_project_settings(
        self, info: ProjectInfo
    ) -> ProjectInfo | None:
        new_info = self._project_settings.exec(info)
        if new_info:
            return new_info
        return None

    ###########################################################################

    def _update_sample_config(
        self, state: State, sample_idx: tuple[str, str]
    ) -> None:
        settings = state.project.settings
        v = self._view

        sel_inst = settings.instruments[sample_idx[0]]
        sel_sample = settings.samples[sample_idx]
        env = sel_sample.envelope

        v.interpolate.setChecked(sel_sample.dyn_interpolate)

        # Instrument dynamics settings
        for dkey, dval in sel_sample.dynamics.items():
            dwidgets = self._dyn_widgets[dkey]
            enable = dkey in sel_inst.dynamics_present
            if not enable:
                dval = 0

            dwidgets.slider.setValue(dval)
            dwidgets.slider.setEnabled(enable)
            dwidgets.setting.setText(pct(dval))
            dwidgets.setting.setEnabled(enable)
            dwidgets.label.setText(hexb(dval))
            dwidgets.label.setEnabled(enable)

        # Instrument articulation settings
        for akey, aval in sel_sample.artics.items():
            awidgets = self._artic_widgets[akey]
            awidgets.length_slider.setValue(aval.length)
            awidgets.length_setting.setText(hexb(aval.length))
            awidgets.volume_slider.setValue(aval.volume)
            awidgets.volume_setting.setText(hexb(aval.volume))
            awidgets.setting_label.setText(hexb(aval.setting))

        # Instrument pan settings
        v.pan_enable.setChecked(sel_sample.pan_enabled)
        v.pan_setting.setEnabled(sel_sample.pan_enabled)
        v.pan_setting_label.setEnabled(sel_sample.pan_enabled)
        v.pan_l_invert.setEnabled(sel_sample.pan_enabled)
        v.pan_r_invert.setEnabled(sel_sample.pan_enabled)
        v.pan_invert_label.setEnabled(sel_sample.pan_enabled)
        v.pan_setting.setValue(sel_sample.pan_setting)
        v.pan_setting_label.setText(sel_sample.pan_description)
        v.pan_l_invert.setChecked(sel_sample.pan_invert[0])
        v.pan_r_invert.setChecked(sel_sample.pan_invert[1])

        # Instrument sample
        v.select_builtin_sample.setChecked(
            sel_sample.sample_source == SampleSource.BUILTIN
        )
        v.builtin_sample.setCurrentIndex(sel_sample.builtin_sample_index)

        samplepack = sel_sample.sample_source == SampleSource.SAMPLEPACK
        v.select_pack_sample.setChecked(samplepack)
        if samplepack:
            with suppress(KeyError):
                v.sample_pack_list.setCurrentItem(
                    self._sample_pack_items[sel_sample.pack_sample]
                )
        else:
            v.sample_pack_list.clearSelection()

        v.sample_settings_box.setEnabled(
            sel_sample.sample_source != SampleSource.BUILTIN
        )

        v.select_brr_sample.setChecked(
            sel_sample.sample_source == SampleSource.BRR
        )

        v.brr_fname.setText("")
        v.brr_size.setText("")
        if fname := sel_sample.brr_fname.name:
            v.brr_fname.setText(str(fname))
            with suppress(FileNotFoundError):
                v.brr_size.setText(
                    brr_size(stat(sel_sample.brr_fname).st_size) + " KB"
                )

        v.octave_shift.setValue(sel_sample.octave_shift)

        v.select_adsr_mode.setChecked(env.adsr_mode)
        v.select_gain_mode.setChecked(not env.adsr_mode)
        v.gain_mode_direct.setChecked(env.gain_mode == GainMode.DIRECT)
        v.gain_mode_inclin.setChecked(env.gain_mode == GainMode.INCLIN)
        v.gain_mode_incbent.setChecked(env.gain_mode == GainMode.INCBENT)
        v.gain_mode_declin.setChecked(env.gain_mode == GainMode.DECLIN)
        v.gain_mode_decexp.setChecked(env.gain_mode == GainMode.DECEXP)
        invert = (not env.adsr_mode) and (env.gain_mode != GainMode.DIRECT)
        v.gain_slider.setInvertedAppearance(invert)
        v.gain_slider.setInvertedControls(invert)
        v.gain_slider.setValue(env.gain_setting)
        v.gain_setting.setText(hexb(env.gain_setting))
        slider = v.attack_slider
        slider.setValue(_slider_inv(slider, env.attack_setting))
        v.attack_setting.setText(hexb(env.attack_setting))
        slider = v.decay_slider
        slider.setValue(_slider_inv(slider, env.decay_setting))
        v.decay_setting.setText(hexb(env.decay_setting))
        v.sus_level_slider.setValue(env.sus_level_setting)
        v.sus_level_setting.setText(hexb(env.sus_level_setting))
        slider = v.sus_rate_slider
        slider.setValue(_slider_inv(slider, env.sus_rate_setting))
        v.sus_rate_setting.setText(hexb(env.sus_rate_setting))

        v.tune_slider.setValue(sel_sample.tune_setting)
        v.tune_setting.setText(hexb(sel_sample.tune_setting))
        v.subtune_slider.setValue(sel_sample.subtune_setting)
        v.subtune_setting.setText(hexb(sel_sample.subtune_setting))

        v.brr_setting.setText(sel_sample.brr_str)

        # Enable dynamics and articulations only when it's not a tracking
        # sample
        v.instrument_articulation_tab.setEnabled(not sel_sample.track)
        v.instrument_dynamics_tab.setEnabled(not sel_sample.track)

        # Apply the more interesting UI updates
        self._update_gain_limits(env.gain_mode == GainMode.DIRECT)
        self._update_envelope(sel_sample.envelope)

    ###########################################################################

    def _update_solomute(self, state: State) -> None:
        for key, sample in state.samples.items():
            solo = to_checkstate(sample.solo)
            mute = to_checkstate(sample.mute)

            item = self._samples[key]
            item.setCheckState(_TblCol.SOLO, solo)
            item.setCheckState(_TblCol.MUTE, mute)

    ###########################################################################

    def _update_unmapped(self, state: State) -> None:
        widget = self._view.multisample_unmapped_list
        widget.clear()

        for pitch, head in reversed(
            sorted(state.unmapped, key=lambda x: x[0].ps)
        ):
            text = pitch.nameWithOctave.replace("-", "♭")
            if head != "normal":
                text += f":{head}"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, (pitch, head))
            widget.addItem(item)

    ###########################################################################

    def _utilization_updated(self, util: Utilization) -> None:
        paint_utilization(
            util, self._view.utilization, self._view.utilization_pct_free
        )

    ###########################################################################
    # Private property definitions
    ###########################################################################

    @property
    def _echo_widgets(self) -> list[QWidget]:
        v = self._view
        return [
            v.echo_filter_0,
            v.echo_filter_1,
            v.echo_left_slider,
            v.echo_left_setting,
            v.echo_left_surround,
            v.echo_left_setting_label,
            v.echo_right_slider,
            v.echo_right_setting,
            v.echo_right_surround,
            v.echo_right_setting_label,
            v.echo_feedback_slider,
            v.echo_feedback_setting,
            v.echo_feedback_surround,
            v.echo_feedback_setting_label,
            v.echo_delay_slider,
            v.echo_delay_setting,
            v.echo_delay_setting_label,
        ]

    ###########################################################################

    @property
    def _loaded(self) -> bool:
        return self._model.loaded

    ###########################################################################

    @property
    def _proj_info(self) -> ProjectInfo:
        return self._state.project.info

    ###########################################################################

    @property
    def _proj_settings(self) -> ProjectSettings:
        return self._state.project.settings

    ###########################################################################

    @property
    def _state(self) -> State:
        return self._model.state

    ###########################################################################

    @property
    def _unsaved(self) -> bool:
        return self._state.unsaved

    ###########################################################################
    @cached_property
    def _view_widgets(self) -> list[QWidget | QAction]:
        widgets = vars(self._view).values()
        return [
            child for child in widgets if isinstance(child, (QWidget, QAction))
        ]
