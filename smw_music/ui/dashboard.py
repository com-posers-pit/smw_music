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
import io
import pkgutil
from collections import deque
from contextlib import ExitStack
from functools import cached_property, partial
from pathlib import Path
from typing import Callable, NamedTuple, cast

# Library imports
from PyQt6 import uic
from PyQt6.QtCore import QEvent, QObject, QSignalBlocker, Qt
from PyQt6.QtGui import QAction, QFont, QIcon, QKeyEvent, QMovie
from PyQt6.QtWidgets import (
    QAbstractSlider,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTreeWidgetItem,
    QWidget,
)

# Package imports
from smw_music import __version__
from smw_music.music_xml.echo import EchoCh
from smw_music.music_xml.instrument import Artic
from smw_music.music_xml.instrument import Dynamics as Dyn
from smw_music.music_xml.instrument import GainMode, SampleSource
from smw_music.ui import resources  # pylint: disable=unused-import
from smw_music.ui.dashboard_view import DashboardView
from smw_music.ui.envelope_preview import EnvelopePreview
from smw_music.ui.model import Model
from smw_music.ui.preferences import Preferences
from smw_music.ui.quotes import labeouf
from smw_music.ui.sample import SamplePack
from smw_music.ui.state import State
from smw_music.utils import hexb, pct

###############################################################################
# Private function definitions
###############################################################################


def _cb_proxy(slot: Callable[[bool], None], state: Qt.CheckState) -> None:
    slot(bool(state))


###############################################################################


def _le_proxy(slot: Callable[[str], None], widget: QLineEdit) -> None:
    slot(widget.text())


###############################################################################


def _mark_unselectable(item: QTableWidgetItem | QTreeWidgetItem) -> None:
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


def _to_checked(checked: bool) -> Qt.CheckState:
    return Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked


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


class _TblCol(enum.IntEnum):
    SOLO = 0
    MUTE = 1
    NAME = 2


###############################################################################
# API class definitions
###############################################################################


class Dashboard(QWidget):
    _history: QMainWindow
    _quicklook: QMainWindow
    _checkitout: QMainWindow
    _envelope_preview: EnvelopePreview
    _extension = "prj"
    _model: Model
    _pref_dlg: Preferences
    _view: DashboardView
    _dyn_widgets: dict[Dyn, _DynamicsWidgets]
    _artic_widgets: dict[Artic, _ArticWidgets]
    _sample_pack_items: dict[tuple[str, Path], QTreeWidgetItem]
    _unsaved: bool
    _project_name: str | None
    _keyhist: deque[int]
    _window_title: str
    _default_tooltips: dict[QWidget | QAction, str]

    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self) -> None:
        super().__init__()
        self._window_title = f"beer v{__version__}"

        self._keyhist = deque(maxlen=len(_KONAMI))
        ui_contents = pkgutil.get_data("smw_music", "/data/dashboard.ui")
        if ui_contents is None:
            raise Exception("Can't locate dashboard")

        self._view: DashboardView = uic.loadUi(io.BytesIO(ui_contents))
        self._view.installEventFilter(self)
        self._view.setWindowTitle(self._window_title)

        self._preferences = Preferences()
        self._model = Model()
        self._unsaved = False
        self._project_name = None
        self._sample_pack_items = {}

        # h/t: https://forum.qt.io/topic/35999/solved-qplaintextedit-how-to-change-the-font-to-be-monospaced/4
        font = QFont("_")
        font.setStyleHint(QFont.StyleHint.Monospace)
        quicklook_edit = QTextEdit()
        quicklook_edit.setFont(font)
        quicklook_edit.setReadOnly(True)
        self._quicklook = QMainWindow(parent=self)
        self._quicklook.setWindowTitle("Quicklook")
        self._quicklook.setMinimumSize(800, 600)
        self._quicklook.setCentralWidget(quicklook_edit)

        self._checkitout = QMainWindow(parent=self)
        self._checkitout.setWindowTitle(
            "Never gonna run around and desert you"
        )
        label = QLabel(self)
        movie = QMovie(parent=self)
        movie.setFileName(":/gifs/ashtley.gif")
        label.setMovie(movie)
        movie.start()
        self._checkitout.setCentralWidget(label)

        self._history = QMainWindow(parent=self)
        self._history.setWindowTitle("Action history")
        self._history.setMinimumSize(800, 600)
        self._history.setCentralWidget(QListWidget())

        self._envelope_preview = EnvelopePreview(self)
        self._history.setWindowTitle("Envelope")

        self._setup_menus()
        self._fix_edit_widths()
        self._combine_widgets()
        self._setup_instrument_table()
        self._attach_signals()
        self._view.generate_and_play.setToolTip(labeouf[0])

        self._default_tooltips = {
            widget: widget.toolTip() for widget in self._view_widgets
        }

        for widget in [
            self._view,
            self._history,
            self._quicklook,
            self._checkitout,
            self._envelope_preview,
        ]:
            widget.setWindowIcon(QIcon(":/icons/maestro.svg"))

        self._view.show()

        self._model.start()

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

        return super().eventFilter(obj, event)

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

    def on_mml_fname_clicked(self) -> None:
        fname, _ = QFileDialog.getSaveFileName(
            self._view, caption="MML Output File", filter="MML Files (*.txt)"
        )

        if fname:
            self._model.on_mml_fname_changed(fname)

    ###########################################################################

    def on_mml_generated(self, mml: str) -> None:
        cast(QTextEdit, self._quicklook.centralWidget()).setText(mml)

    ###########################################################################

    def on_musicxml_fname_clicked(self) -> None:
        fname, _ = QFileDialog.getOpenFileName(
            self._view,
            caption="MusicXML Input File",
            filter="MusicXML Files (*.musicxml *.mxl)",
        )
        if fname:
            self._model.on_musicxml_fname_changed(fname)

    ###########################################################################

    def on_open_history_clicked(self) -> None:
        self._history.show()

    ###########################################################################

    def on_open_quicklook_clicked(self) -> None:
        self._quicklook.show()

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
        sample_packs: dict[str, SamplePack],
    ) -> None:
        v = self._view  # pylint: disable=invalid-name

        # advance_enabled handling
        v.generate_mml.setVisible(advanced_enabled)
        v.generate_spc.setVisible(advanced_enabled)
        v.play_spc.setVisible(advanced_enabled)
        v.other_settings_box.setVisible(advanced_enabled)

        # amk_valid handling
        for action in [
            v.new_project,
            v.open_project,
            v.save_project,
            v.menuRecent_Projects,
        ]:
            enable = amk_valid and spcplayer_valid

            tooltip = (
                "Define AMK zip file and spcplayer executable in "
                "preferences to enable this"
            )

            if enable:
                tooltip = self._default_tooltips[action]

            action.setToolTip(tooltip)
            action.setEnabled(enable)

        # sample_packs handling
        self._sample_pack_items = {}
        tree = self._view.sample_pack_list  # pylint: disable=invalid-name

        tree.clear()

        for name, pack in sample_packs.items():
            top = QTreeWidgetItem(tree, [name])
            _mark_unselectable(top)

            self._add_sample_pack(top, name, pack)
            tree.addTopLevelItem(top)

    ###########################################################################

    def on_preview_envelope_clicked(self) -> None:
        self._envelope_preview.show()

    ###########################################################################

    def on_recent_projects_updated(self, projects: list[Path]) -> None:
        menu = cast(QMenu, self._view.menuRecent_Projects)
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

    def on_state_changed(self, state: State, update_instruments: bool) -> None:
        if update_instruments:
            self._update_instruments([inst.name for inst in state.instruments])

        v = self._view  # pylint: disable=invalid-name
        inst = state.inst
        self._unsaved = state.unsaved
        self._project_name = state.project_name

        if self._project_name is None:
            title = "[No project]"
        else:
            title = f"[{self._project_name}]"
            if self._unsaved:
                title += " +"

        title += f" - {self._window_title}"
        v.setWindowTitle(title)

        with ExitStack() as stack:
            for child in self._view_widgets:
                stack.enter_context(QSignalBlocker(child))

            # Control Panel
            v.musicxml_fname.setText(state.musicxml_fname)
            v.mml_fname.setText(state.mml_fname)
            v.porter_name.setText(state.porter)
            v.game_name.setText(state.game)
            v.loop_analysis.setChecked(state.loop_analysis)
            v.superloop_analysis.setChecked(state.superloop_analysis)
            v.measure_numbers.setChecked(state.measure_numbers)
            v.start_measure.setValue(state.start_measure)

            v.reload_musicxml.setEnabled(bool(state.musicxml_fname))

            standalone_mode = state.project_name is None
            project_mode = not standalone_mode

            v.generate_and_play.setEnabled(project_mode)
            v.generate_spc.setEnabled(project_mode)
            v.play_spc.setEnabled(project_mode)
            v.save_project.setEnabled(project_mode)
            v.close_project.setEnabled(project_mode)
            v.select_mml_fname.setEnabled(standalone_mode)
            v.mml_fname.setEnabled(standalone_mode)

            # Solo/mute settings
            inst_list = self._view.instrument_list
            inst_idx = state.instrument_idx
            if inst_idx is not None:
                inst_list.setCurrentCell(inst_idx, _TblCol.NAME)

            v.mute_percussion.setChecked(state.mute_percussion)
            v.solo_percussion.setChecked(state.solo_percussion)

            for row, inst_cfg in enumerate(state.instruments):
                solo = _to_checked(inst_cfg.solo)
                mute = _to_checked(inst_cfg.mute)
                inst_list.item(row, _TblCol.SOLO.value).setCheckState(solo)
                inst_list.item(row, _TblCol.MUTE.value).setCheckState(mute)

            # Instrument dynamics settings
            for dkey, dval in inst.dynamics.items():
                dwidgets = self._dyn_widgets[dkey]
                enable = dkey in inst.dynamics_present

                dwidgets.slider.setValue(dval)
                dwidgets.slider.setEnabled(enable)
                dwidgets.setting.setText(pct(dval))
                dwidgets.setting.setEnabled(enable)
                dwidgets.label.setText(hexb(dval))
                dwidgets.label.setEnabled(enable)

            # Instrument articulation settings
            for akey, aval in inst.artics.items():
                awidgets = self._artic_widgets[akey]
                awidgets.length_slider.setValue(aval.length)
                awidgets.length_setting.setText(hexb(aval.length))
                awidgets.volume_slider.setValue(aval.volume)
                awidgets.volume_setting.setText(hexb(aval.volume))
                awidgets.setting_label.setText(hexb(aval.setting))

            # Instrument pan settings
            v.pan_enable.setChecked(inst.pan_enabled)
            v.pan_setting.setEnabled(inst.pan_enabled)
            v.pan_setting_label.setEnabled(inst.pan_enabled)
            v.pan_l_invert.setEnabled(inst.pan_enabled)
            v.pan_r_invert.setEnabled(inst.pan_enabled)
            v.pan_invert_label.setEnabled(inst.pan_enabled)
            v.pan_setting.setValue(inst.pan_setting)
            v.pan_setting_label.setText(inst.pan_description)
            v.pan_l_invert.setChecked(inst.pan_invert[0])
            v.pan_r_invert.setChecked(inst.pan_invert[1])

            # Instrument sample
            v.select_builtin_sample.setChecked(
                inst.sample_source == SampleSource.BUILTIN
            )
            v.builtin_sample.setCurrentIndex(inst.builtin_sample_index)
            v.select_pack_sample.setChecked(
                inst.sample_source == SampleSource.SAMPLEPACK
            )
            v.sample_settings_box.setEnabled(
                inst.sample_source != SampleSource.BUILTIN
            )
            try:
                v.sample_pack_list.setCurrentItem(
                    self._sample_pack_items[state.inst.pack_sample]
                )
            except KeyError:
                pass

            v.select_brr_sample.setChecked(
                inst.sample_source == SampleSource.BRR
            )
            fname = str(inst.brr_fname) if inst.brr_fname.name else ""
            v.brr_fname.setText(fname)
            v.octave.setValue(inst.octave)

            v.select_adsr_mode.setChecked(inst.adsr_mode)
            v.select_gain_mode.setChecked(not inst.adsr_mode)
            v.gain_mode_direct.setChecked(inst.gain_mode == GainMode.DIRECT)
            v.gain_mode_inclin.setChecked(inst.gain_mode == GainMode.INCLIN)
            v.gain_mode_incbent.setChecked(inst.gain_mode == GainMode.INCBENT)
            v.gain_mode_declin.setChecked(inst.gain_mode == GainMode.DECLIN)
            v.gain_mode_decexp.setChecked(inst.gain_mode == GainMode.DECEXP)
            v.gain_slider.setValue(inst.gain_setting)
            v.gain_setting.setText(hexb(inst.gain_setting))
            v.attack_slider.setValue(inst.attack_setting)
            v.attack_setting.setText(hexb(inst.attack_setting))
            v.decay_slider.setValue(inst.decay_setting)
            v.decay_setting.setText(hexb(inst.decay_setting))
            v.sus_level_slider.setValue(inst.sus_level_setting)
            v.sus_level_setting.setText(hexb(inst.sus_level_setting))
            v.sus_rate_slider.setValue(inst.sus_rate_setting)
            v.sus_rate_setting.setText(hexb(inst.sus_rate_setting))

            v.tune_slider.setValue(inst.tune_setting)
            v.tune_setting.setText(hexb(inst.tune_setting))
            v.subtune_slider.setValue(inst.subtune_setting)
            v.subtune_setting.setText(hexb(inst.subtune_setting))

            v.brr_setting.setText(inst.brr_str)

            # Global settings
            v.global_volume_slider.setValue(state.global_volume)
            v.global_volume_setting.setText(pct(state.global_volume))
            v.global_volume_setting_label.setText(hexb(state.global_volume))
            v.global_legato.setChecked(state.global_legato)

            v.echo_enable.setChecked(state.global_echo_enable)
            v.echo_ch0.setChecked(EchoCh.CH0 in state.echo.enables)
            v.echo_ch1.setChecked(EchoCh.CH1 in state.echo.enables)
            v.echo_ch2.setChecked(EchoCh.CH2 in state.echo.enables)
            v.echo_ch3.setChecked(EchoCh.CH3 in state.echo.enables)
            v.echo_ch4.setChecked(EchoCh.CH4 in state.echo.enables)
            v.echo_ch5.setChecked(EchoCh.CH5 in state.echo.enables)
            v.echo_ch6.setChecked(EchoCh.CH6 in state.echo.enables)
            v.echo_ch7.setChecked(EchoCh.CH7 in state.echo.enables)
            v.echo_filter_0.setChecked(state.echo.fir_filt == 0)
            v.echo_filter_1.setChecked(state.echo.fir_filt == 1)

            v.echo_left_slider.setValue(
                int(v.echo_left_slider.maximum() * state.echo.vol_mag[0])
            )
            v.echo_left_setting.setText(pct(state.echo.vol_mag[0], 1.0))
            v.echo_left_surround.setChecked(state.echo.vol_inv[0])
            v.echo_left_setting_label.setText(hexb(state.echo.left_vol_reg))
            v.echo_right_slider.setValue(
                int(v.echo_right_slider.maximum() * state.echo.vol_mag[1])
            )
            v.echo_right_setting.setText(pct(state.echo.vol_mag[1], 1.0))
            v.echo_right_surround.setChecked(state.echo.vol_inv[1])
            v.echo_right_setting_label.setText(hexb(state.echo.right_vol_reg))
            v.echo_feedback_slider.setValue(
                int(v.echo_feedback_slider.maximum() * state.echo.fb_mag)
            )
            v.echo_feedback_setting.setText(pct(state.echo.fb_mag, 1.0))
            v.echo_feedback_surround.setChecked(state.echo.fb_inv)
            v.echo_feedback_setting_label.setText(hexb(state.echo.fb_reg))
            v.echo_delay_slider.setValue(state.echo.delay)
            v.echo_delay_setting.setText(hexb(state.echo.delay))
            v.echo_delay_setting_label.setText(f"{16*state.echo.delay}ms")

            for widget in self._echo_widgets:
                widget.setEnabled(state.global_echo_enable)

            # Apply the more interesting UI updates
            self._update_gain_limits(inst.gain_mode == GainMode.DIRECT)
            self._update_envelope(
                inst.adsr_mode,
                inst.attack_setting,
                inst.decay_setting,
                inst.sus_level_setting,
                inst.sus_rate_setting,
                inst.gain_mode,
                inst.gain_setting,
            )

    ###########################################################################

    def on_status_updated(self, msg: str) -> None:
        cast(QListWidget, self._history.centralWidget()).insertItem(0, msg)
        self._view.statusBar().showMessage(msg)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _about(self) -> None:
        title = "About MusicXML -> MML"
        text = f"Version: {__version__}"
        text += "\nCopyright Ⓒ 2023 The SMW Music Python Project Authors"
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

            item = QTreeWidgetItem(parent, [sample.path.name])
            item_id = (name, sample.path)
            item.setData(0, Qt.ItemDataRole.UserRole, item_id)
            self._sample_pack_items[item_id] = item

    ###########################################################################

    def _attach_signals(self) -> None:  # pylint: disable=too-many-statements
        m = self._model  # pylint: disable=invalid-name
        v = self._view  # pylint: disable=invalid-name

        # Short aliases to avoid line wrapping
        alen = m.on_artic_length_changed
        avol = m.on_artic_volume_changed

        connections: list[tuple[QWidget, Callable[..., None]]] = [
            # Control Panel
            (v.select_musicxml_fname, self.on_musicxml_fname_clicked),
            (v.musicxml_fname, m.on_musicxml_fname_changed),
            (v.select_mml_fname, self.on_mml_fname_clicked),
            (v.mml_fname, m.on_mml_fname_changed),
            (v.porter_name, m.on_porter_name_changed),
            (v.game_name, m.on_game_name_changed),
            (v.loop_analysis, m.on_loop_analysis_changed),
            (v.superloop_analysis, m.on_superloop_analysis_changed),
            (v.measure_numbers, m.on_measure_numbers_changed),
            (v.start_measure, m.on_start_measure_changed),
            (v.open_quicklook, self.on_open_quicklook_clicked),
            (v.open_history, self.on_open_history_clicked),
            (v.generate_mml, m.on_generate_mml_clicked),
            (v.generate_spc, m.on_generate_spc_clicked),
            (v.play_spc, m.on_play_spc_clicked),
            (v.generate_and_play, m.on_generate_and_play_clicked),
            (v.generate_and_play, self._update_generate_and_play_tooltip),
            (v.reload_musicxml, m.on_reload_musicxml_clicked),
            # Instrument settings
            (v.instrument_list, m.on_instrument_changed),
            (v.interpolate, m.on_interpolate_changed),
            (v.mute_percussion, m.on_mute_percussion_changed),
            (v.solo_percussion, m.on_solo_percussion_changed),
            # Instrument pan settings
            (v.pan_enable, m.on_pan_enable_changed),
            (v.pan_setting, m.on_pan_setting_changed),
            (v.pan_l_invert, partial(m.on_pan_invert_changed, True)),
            (v.pan_r_invert, partial(m.on_pan_invert_changed, False)),
            # Instrument sample
            (v.select_builtin_sample, m.on_builtin_sample_selected),
            (v.builtin_sample, m.on_builtin_sample_changed),
            (v.select_pack_sample, m.on_pack_sample_selected),
            (v.select_brr_sample, m.on_brr_sample_selected),
            (v.select_brr_fname, self.on_brr_clicked),
            (v.brr_fname, m.on_brr_fname_changed),
            (v.octave, m.on_octave_changed),
            (v.select_adsr_mode, m.on_select_adsr_mode_selected),
            (v.gain_mode_direct, m.on_gain_direct_selected),
            (v.gain_mode_inclin, m.on_gain_inclin_selected),
            (v.gain_mode_incbent, m.on_gain_incbent_selected),
            (v.gain_mode_declin, m.on_gain_declin_selected),
            (v.gain_mode_decexp, m.on_gain_decexp_selected),
            (v.gain_slider, m.on_gain_changed),
            (v.gain_setting, m.on_gain_changed),
            (v.attack_slider, m.on_attack_changed),
            (v.attack_setting, m.on_attack_changed),
            (v.decay_slider, m.on_decay_changed),
            (v.decay_setting, m.on_decay_changed),
            (v.sus_level_slider, m.on_sus_level_changed),
            (v.sus_level_setting, m.on_sus_level_changed),
            (v.sus_rate_slider, m.on_sus_rate_changed),
            (v.sus_rate_setting, m.on_sus_rate_changed),
            (v.tune_slider, m.on_tune_changed),
            (v.tune_setting, m.on_tune_changed),
            (v.subtune_slider, m.on_subtune_changed),
            (v.subtune_setting, m.on_subtune_changed),
            (v.brr_setting, m.on_brr_setting_changed),
            (v.preview_envelope, self.on_preview_envelope_clicked),
            # Global settings
            (v.global_volume_slider, m.on_global_volume_changed),
            (v.global_volume_setting, m.on_global_volume_changed),
            (v.global_legato, m.on_global_legato_changed),
            (v.echo_enable, m.on_global_echo_en_changed),
            (v.echo_ch0, partial(m.on_echo_en_changed, EchoCh.CH0)),
            (v.echo_ch1, partial(m.on_echo_en_changed, EchoCh.CH1)),
            (v.echo_ch2, partial(m.on_echo_en_changed, EchoCh.CH2)),
            (v.echo_ch3, partial(m.on_echo_en_changed, EchoCh.CH3)),
            (v.echo_ch4, partial(m.on_echo_en_changed, EchoCh.CH4)),
            (v.echo_ch5, partial(m.on_echo_en_changed, EchoCh.CH5)),
            (v.echo_ch6, partial(m.on_echo_en_changed, EchoCh.CH6)),
            (v.echo_ch7, partial(m.on_echo_en_changed, EchoCh.CH7)),
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
        ]

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
            elif isinstance(widget, QTableWidget):
                pass
                # widget.currentRowChanged.connect(slot)
            else:
                # This is basically a compile-time exception
                raise Exception(f"Unhandled widget connection {widget}")

        v.instrument_list.itemChanged.connect(self._on_solomute_change)
        v.instrument_list.itemSelectionChanged.connect(self._on_inst_change)
        v.sample_pack_list.itemSelectionChanged.connect(
            self.on_pack_sample_changed
        )

        # Return signals
        m.state_changed.connect(self.on_state_changed)
        m.mml_generated.connect(self.on_mml_generated)
        m.response_generated.connect(self.on_response_generated)
        m.preferences_changed.connect(self.on_preferences_changed)
        m.recent_projects_updated.connect(self.on_recent_projects_updated)
        v.actionClearRecentProjects.triggered.connect(
            m.on_recent_projects_cleared
        )
        m.status_updated.connect(self.on_status_updated)

    ###########################################################################

    def _combine_widgets(self) -> None:
        v = self._view  # pylint: disable=invalid-name
        self._dyn_widgets = {}
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
            self._model.create_project(Path(proj_dir))

    ###########################################################################

    def _fix_edit_widths(self) -> None:
        v = self._view  # pylint: disable=invalid-name
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

    def _on_close_project_clicked(self) -> None:
        close = self._prompt_to_save()
        if close != QMessageBox.StandardButton.Cancel:
            self._model.close_project()

    ###########################################################################

    def _on_inst_change(self) -> None:
        widget = self._view.instrument_list
        self._model.on_instrument_changed(widget.currentRow())

    ###########################################################################

    def _on_solomute_change(self, item: QTableWidgetItem) -> None:
        role: tuple[_TblCol, int] | None = item.data(Qt.ItemDataRole.UserRole)
        if role:
            row = role[1]
            checked = item.checkState() == Qt.CheckState.Checked
            if role[0] == _TblCol.SOLO:
                self._model.on_solo_changed(row, checked)
            if role[0] == _TblCol.MUTE:
                self._model.on_mute_changed(row, checked)

    ###########################################################################

    def _open_project(self) -> None:
        fname, _ = QFileDialog.getOpenFileName(
            self._view, "Project File", filter=f"*.{self._extension}"
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
        if self._unsaved and self._project_name is not None:
            quit_msg = "Save project before closing?"
            reply = QMessageBox.question(
                self._view,
                "Save project",
                quit_msg,
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._model.on_save()
        return reply

    ###########################################################################

    def _setup_instrument_table(self) -> None:
        widget = self._view.instrument_list
        solo_item = QTableWidgetItem("S")
        solo_item.setToolTip("Solo Instrument")
        mute_item = QTableWidgetItem("M")
        mute_item.setToolTip("Mute Instrument")

        widget.setHorizontalHeaderItem(0, solo_item)
        widget.setHorizontalHeaderItem(1, mute_item)
        widget.setHorizontalHeaderItem(2, QTableWidgetItem("Instrument"))
        widget.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

    ###########################################################################

    def _setup_menus(self) -> None:
        view = self._view
        model = self._model

        view.new_project.triggered.connect(self._create_project)
        view.open_project.triggered.connect(self._open_project)
        view.save_project.triggered.connect(model.on_save)
        view.close_project.triggered.connect(self._on_close_project_clicked)
        view.open_preferences.triggered.connect(self._open_preferences)
        view.exit_dashboard.triggered.connect(QApplication.quit)

        view.undo.triggered.connect(model.on_undo_clicked)
        view.redo.triggered.connect(model.on_redo_clicked)

        view.show_about.triggered.connect(self._about)
        view.show_about_qt.triggered.connect(QApplication.aboutQt)

    ###########################################################################

    def _update_envelope(  # pylint: disable=too-many-arguments
        self,
        adsr_mode: bool,
        attack_reg: int,
        decay_reg: int,
        sus_level_reg: int,
        sus_rate_reg: int,
        gain_mode: GainMode,
        gain_reg: int,
    ) -> None:
        env = self._envelope_preview
        view = self._view

        if adsr_mode:
            labels = env.plot_adsr(
                attack_reg, decay_reg, sus_level_reg, sus_rate_reg
            )
            view.attack_eu_label.setText(labels[0])
            view.decay_eu_label.setText(labels[1])
            view.sus_level_eu_label.setText(labels[2])
            view.sus_rate_eu_label.setText(labels[3])
        else:  # gain mode
            match gain_mode:
                case GainMode.DIRECT:
                    label = env.plot_direct_gain(gain_reg)
                case GainMode.INCLIN:
                    label = env.plot_inclin(gain_reg)
                case GainMode.INCBENT:
                    label = env.plot_incbent(gain_reg)
                case GainMode.DECLIN:
                    label = env.plot_declin(gain_reg)
                case GainMode.DECEXP:
                    label = env.plot_decexp(gain_reg)
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

    def _update_generate_and_play_tooltip(self) -> None:
        widget = self._view.generate_and_play
        tooltip = widget.toolTip()
        idx = (labeouf.index(tooltip) + 1) % len(labeouf)
        widget.setToolTip(labeouf[idx])

    ###########################################################################

    def _update_instruments(self, names: list[str]) -> None:
        widget = self._view.instrument_list

        with QSignalBlocker(widget):
            widget.clearContents()
            widget.setRowCount(len(names))

            for row, name in enumerate(names):
                solo_box = QTableWidgetItem()
                solo_box.setCheckState(Qt.CheckState.Unchecked)
                solo_box.setData(Qt.ItemDataRole.UserRole, (_TblCol.SOLO, row))
                solo_box.setToolTip(f"Solo {name}")
                _mark_unselectable(solo_box)

                mute_box = QTableWidgetItem()
                mute_box.setCheckState(Qt.CheckState.Unchecked)
                mute_box.setData(Qt.ItemDataRole.UserRole, (_TblCol.MUTE, row))
                mute_box.setToolTip(f"Mute {name}")
                _mark_unselectable(mute_box)

                name_box = QTableWidgetItem(name)
                name_box.setFlags(
                    name_box.flags() & ~Qt.ItemFlag.ItemIsEditable
                )

                widget.setItem(row, 0, solo_box)
                widget.setItem(row, 1, mute_box)
                widget.setItem(row, 2, name_box)

    ###########################################################################
    # Private property definitions
    ###########################################################################

    @property
    def _echo_widgets(self) -> list[QWidget]:
        v = self._view  # pylint: disable=invalid-name
        return [
            v.echo_ch0,
            v.echo_ch1,
            v.echo_ch2,
            v.echo_ch3,
            v.echo_ch4,
            v.echo_ch5,
            v.echo_ch6,
            v.echo_ch7,
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

    @cached_property
    def _view_widgets(self) -> list[QWidget | QAction]:
        widgets = vars(self._view).values()
        return [
            child for child in widgets if isinstance(child, (QWidget, QAction))
        ]
