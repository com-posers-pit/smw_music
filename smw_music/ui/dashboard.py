#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Dashboard application."""

###############################################################################
# Imports
###############################################################################

# Standard library imports
import io
import pathlib
import pkgutil
from functools import partial

# Library imports
from PyQt6 import uic
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QAbstractSlider,
    QApplication,
    QCheckBox,
    QFileDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSlider,
    QTextEdit,
)

# Package imports
from smw_music import __version__
from smw_music.music_xml.echo import EchoConfig
from smw_music.music_xml.song import Song
from smw_music.ui.envelope_preview import EnvelopePreview
from smw_music.ui.model import Model
from smw_music.ui.preferences import Preferences
from smw_music.ui.state import Artic
from smw_music.ui.state import Dynamics as Dyn
from smw_music.ui.state import EchoCh, GainMode, SampleSource, State
from smw_music.utils import hexb, pct

###############################################################################
# Private class definitions
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
# API class definitions
###############################################################################


class Dashboard:
    _edit: QTextEdit
    _quicklook: QMainWindow
    _envelope_preview: EnvelopePreview
    _extension = "prj"
    _model: Model
    _pref_dlg: Preferences
    _view: QMainWindow

    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self):
        ui_contents = pkgutil.get_data("smw_music", "/data/dashboard.ui")
        if ui_contents is None:
            raise Exception("Can't locate dashboard")

        self._view = uic.loadUi(io.BytesIO(ui_contents))
        self._preferences = Preferences()
        self._model = Model()

        self._edit = QTextEdit()
        self._quicklook = QMainWindow(parent=self._view)
        self._quicklook.setMinimumSize(800, 600)
        self._quicklook.setCentralWidget(self._edit)

        self._envelope_preview = EnvelopePreview(self._view)

        self._view.sample_pack_list.setModel(self._model.sample_packs_model)

        self._setup_menus()
        self._fix_edit_widths()
        self._attach_signals()

        self._view.show()

        self._model.reinforce_state()

    ###########################################################################
    # API signal definitions
    ###########################################################################

    def on_brr_clicked(self) -> None:
        fname, _ = QFileDialog.getOpenFileName(
            self._view, caption="BRR Sample File", filter="BRR Files (*.brr)"
        )
        if fname:
            self._model.on_brr_fname_changed(fname)

    ###########################################################################

    def on_instruments_changed(self, names: list[str]) -> None:
        widget = self._view.instrument_list
        widget.clear()
        for name in names:
            widget.addItem(name)

    ###########################################################################

    def on_mml_fname_clicked(self) -> None:
        fname, _ = QFileDialog.getSaveFileName(
            self._view, caption="MML Output File", filter="MML Files (*.txt)"
        )

        if fname:
            self._model.on_mml_fname_changed(fname)

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

    def on_open_quicklook_clicked(self) -> None:
        self._quicklook.show()

    ###########################################################################

    def on_preview_envelope_clicked(self) -> None:
        self._envelope_preview.show()

    ###########################################################################

    def on_state_changed(self, state: State) -> None:
        v = self._view  # pylint: disable=invalid-name

        # Control Panel
        v.musicxml_fname.setText(state.musicxml_fname)
        v.mml_fname.setText(state.mml_fname)
        v.loop_analysis.setChecked(state.loop_analysis)
        v.superloop_analysis.setChecked(state.superloop_analysis)
        v.measure_numbers.setChecked(state.measure_numbers)

        # Instrument dynamics settings
        dynamics = state.dynamics_settings
        v.pppp_slider.setValue(dynamics[Dyn.PPPP])
        v.pppp_setting.setText(pct(dynamics[Dyn.PPPP]))
        v.pppp_setting_label.setText(hexb(dynamics[Dyn.PPPP]))
        v.ppp_slider.setValue(dynamics[Dyn.PPP])
        v.ppp_setting.setText(pct(dynamics[Dyn.PPP]))
        v.ppp_setting_label.setText(hexb(dynamics[Dyn.PPP]))
        v.pp_slider.setValue(dynamics[Dyn.PP])
        v.pp_setting.setText(pct(dynamics[Dyn.PP]))
        v.pp_setting_label.setText(hexb(dynamics[Dyn.PP]))
        v.p_slider.setValue(dynamics[Dyn.P])
        v.p_setting.setText(pct(dynamics[Dyn.P]))
        v.p_setting_label.setText(hexb(dynamics[Dyn.P]))
        v.mp_slider.setValue(dynamics[Dyn.MP])
        v.mp_setting.setText(pct(dynamics[Dyn.MP]))
        v.mp_setting_label.setText(hexb(dynamics[Dyn.MP]))
        v.mf_slider.setValue(dynamics[Dyn.MF])
        v.mf_setting.setText(pct(dynamics[Dyn.MF]))
        v.mf_setting_label.setText(hexb(dynamics[Dyn.MF]))
        v.f_slider.setValue(dynamics[Dyn.F])
        v.f_setting.setText(pct(dynamics[Dyn.F]))
        v.f_setting_label.setText(hexb(dynamics[Dyn.F]))
        v.ff_slider.setValue(dynamics[Dyn.FF])
        v.ff_setting.setText(pct(dynamics[Dyn.FF]))
        v.ff_setting_label.setText(hexb(dynamics[Dyn.FF]))
        v.fff_slider.setValue(dynamics[Dyn.FFF])
        v.fff_setting.setText(pct(dynamics[Dyn.FFF]))
        v.fff_setting_label.setText(hexb(dynamics[Dyn.FFF]))
        v.ffff_slider.setValue(dynamics[Dyn.FFFF])
        v.ffff_setting.setText(pct(dynamics[Dyn.FFFF]))
        v.ffff_setting_label.setText(hexb(dynamics[Dyn.FFFF]))
        v.interpolate.setChecked(state.dyn_interpolate)

        # Instrument articulation settings
        artic = state.artic_settings[Artic.DEFAULT]
        v.artic_default_length_slider.setValue(artic.length)
        v.artic_default_length_setting.setText(hexb(artic.length))
        v.artic_default_volume_slider.setValue(artic.volume)
        v.artic_default_volume_setting.setText(hexb(artic.volume))
        v.artic_default_setting_label.setText(hexb(artic.setting))
        artic = state.artic_settings[Artic.ACCENT]
        v.artic_acc_length_slider.setValue(artic.length)
        v.artic_acc_length_setting.setText(hexb(artic.length))
        v.artic_acc_volume_slider.setValue(artic.volume)
        v.artic_acc_volume_setting.setText(hexb(artic.volume))
        v.artic_acc_setting_label.setText(hexb(artic.setting))
        artic = state.artic_settings[Artic.STACCATO]
        v.artic_stacc_length_slider.setValue(artic.length)
        v.artic_stacc_length_setting.setText(hexb(artic.length))
        v.artic_stacc_volume_slider.setValue(artic.volume)
        v.artic_stacc_volume_setting.setText(hexb(artic.volume))
        v.artic_stacc_setting_label.setText(hexb(artic.setting))
        artic = state.artic_settings[Artic.ACCSTAC]
        v.artic_accstacc_length_slider.setValue(artic.length)
        v.artic_accstacc_length_setting.setText(hexb(artic.length))
        v.artic_accstacc_volume_slider.setValue(artic.volume)
        v.artic_accstacc_volume_setting.setText(hexb(artic.volume))
        v.artic_accstacc_setting_label.setText(hexb(artic.setting))

        # Instrument pan settings
        v.pan_enable.setChecked(state.pan_enabled)
        v.pan_setting.setEnabled(state.pan_enabled)
        v.pan_setting_label.setEnabled(state.pan_enabled)
        v.pan_setting.setValue(state.pan_setting)
        v.pan_setting_label.setText(state.pan_description)

        # Instrument sample
        v.select_builtin_sample.setChecked(
            state.sample_source == SampleSource.BUILTIN
        )
        v.builtin_sample.setCurrentIndex(state.builtin_sample_index)
        v.select_pack_sample.setChecked(
            state.sample_source == SampleSource.SAMPLEPACK
        )
        # v.sample_pack_list.setCurrentIndex(state.pack_sample_index)
        v.select_brr_sample.setChecked(state.sample_source == SampleSource.BRR)
        v.brr_fname.setText(state.brr_fname)

        v.select_adsr_mode.setChecked(state.adsr_mode)
        v.select_gain_mode.setChecked(not state.adsr_mode)
        v.gain_mode_direct.setChecked(state.gain_mode == GainMode.DIRECT)
        v.gain_mode_inclin.setChecked(state.gain_mode == GainMode.INCLIN)
        v.gain_mode_incbent.setChecked(state.gain_mode == GainMode.INCBENT)
        v.gain_mode_declin.setChecked(state.gain_mode == GainMode.DECLIN)
        v.gain_mode_decexp.setChecked(state.gain_mode == GainMode.DECEXP)
        v.gain_slider.setValue(state.gain_setting)
        v.gain_setting.setText(hexb(state.gain_setting))
        v.attack_slider.setValue(state.attack_setting)
        v.attack_setting.setText(hexb(state.attack_setting))
        v.decay_slider.setValue(state.decay_setting)
        v.decay_setting.setText(hexb(state.decay_setting))
        v.sus_level_slider.setValue(state.sus_level_setting)
        v.sus_level_setting.setText(hexb(state.sus_level_setting))
        v.sus_rate_slider.setValue(state.sus_rate_setting)
        v.sus_rate_setting.setText(hexb(state.sus_rate_setting))

        v.tune_slider.setValue(state.tune_setting)
        v.tune_setting.setText(hexb(state.tune_setting))
        v.subtune_slider.setValue(state.subtune_setting)
        v.subtune_setting.setText(hexb(state.subtune_setting))

        v.brr_setting.setText(" ".join(hexb(x) for x in state.brr_setting))

        # Global settings
        v.global_volume_slider.setValue(state.global_volume)
        v.global_volume_setting.setText(pct(state.global_volume))
        v.global_volume_setting_label.setText(hexb(state.global_volume))
        v.global_legato.setChecked(state.global_legato)
        v.echo_enable.setChecked(state.echo_enable[EchoCh.GLOBAL])
        v.echo_ch0.setChecked(state.echo_enable[EchoCh.CH0])
        v.echo_ch1.setChecked(state.echo_enable[EchoCh.CH1])
        v.echo_ch2.setChecked(state.echo_enable[EchoCh.CH2])
        v.echo_ch3.setChecked(state.echo_enable[EchoCh.CH3])
        v.echo_ch4.setChecked(state.echo_enable[EchoCh.CH4])
        v.echo_ch5.setChecked(state.echo_enable[EchoCh.CH5])
        v.echo_ch6.setChecked(state.echo_enable[EchoCh.CH6])
        v.echo_ch7.setChecked(state.echo_enable[EchoCh.CH7])
        v.echo_filter_0.setChecked(state.echo_filter0)
        v.echo_filter_1.setChecked(not state.echo_filter0)
        v.echo_left_slider.setValue(state.echo_left_setting)
        v.echo_left_setting.setText(hexb(state.echo_left_setting))
        v.echo_left_surround.setChecked(False)  # TODO
        v.echo_right_slider.setValue(state.echo_right_setting)
        v.echo_right_setting.setText(hexb(state.echo_right_setting))
        v.echo_right_surround.setChecked(False)  # TODO
        v.echo_feedback_slider.setValue(state.echo_feedback_setting)
        v.echo_feedback_setting.setText(hexb(state.echo_feedback_setting))
        v.echo_feedback_surround.setChecked(False)  # TODO
        v.echo_delay_slider.setValue(state.echo_delay_setting)
        v.echo_delay_setting.setText(hexb(state.echo_delay_setting))

        # Apply the more interesting UI updates
        self._update_gain_limits(state.gain_mode == GainMode.DIRECT)
        self._update_envelope(
            state.adsr_mode,
            state.attack_setting,
            state.decay_setting,
            state.sus_level_setting,
            state.sus_rate_setting,
            state.gain_mode,
            state.gain_setting,
        )

    ###########################################################################

    def update_song(self, song: Song) -> None:
        pass
        # self._volume.set_volume(song.volume)

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

    def _attach_signals(self) -> None:  # pylint: disable=too-many-statements
        m = self._model  # pylint: disable=invalid-name
        v = self._view  # pylint: disable=invalid-name

        # Short aliases to avoid line wrapping
        alen = m.on_artic_length_changed
        avol = m.on_artic_volume_changed

        connections = [
            # Control Panel
            (v.select_musicxml_fname, self.on_musicxml_fname_clicked),
            (v.musicxml_fname, m.on_musicxml_fname_changed),
            (v.select_mml_fname, self.on_mml_fname_clicked),
            (v.mml_fname, m.on_mml_fname_changed),
            (v.loop_analysis, m.on_loop_analysis_changed),
            (v.superloop_analysis, m.on_superloop_analysis_changed),
            (v.measure_numbers, m.on_measure_numbers_changed),
            (v.open_quicklook, self.on_open_quicklook_clicked),
            (v.generate_mml, m.on_generate_mml_clicked),
            (v.generate_spc, m.on_generate_spc_clicked),
            (v.play_spc, m.on_play_spc_clicked),
            # Instrument dynamics settings
            (v.pppp_slider, partial(m.on_dynamics_changed, Dyn.PPPP)),
            (v.pppp_setting, partial(m.on_dynamics_changed, Dyn.PPPP)),
            (v.ppp_slider, partial(m.on_dynamics_changed, Dyn.PPP)),
            (v.ppp_setting, partial(m.on_dynamics_changed, Dyn.PPP)),
            (v.pp_slider, partial(m.on_dynamics_changed, Dyn.PP)),
            (v.pp_setting, partial(m.on_dynamics_changed, Dyn.PP)),
            (v.p_slider, partial(m.on_dynamics_changed, Dyn.P)),
            (v.p_setting, partial(m.on_dynamics_changed, Dyn.P)),
            (v.mp_slider, partial(m.on_dynamics_changed, Dyn.MP)),
            (v.mp_setting, partial(m.on_dynamics_changed, Dyn.MP)),
            (v.mf_slider, partial(m.on_dynamics_changed, Dyn.MF)),
            (v.mf_setting, partial(m.on_dynamics_changed, Dyn.MF)),
            (v.f_slider, partial(m.on_dynamics_changed, Dyn.F)),
            (v.f_setting, partial(m.on_dynamics_changed, Dyn.F)),
            (v.ff_slider, partial(m.on_dynamics_changed, Dyn.FF)),
            (v.ff_setting, partial(m.on_dynamics_changed, Dyn.FF)),
            (v.fff_slider, partial(m.on_dynamics_changed, Dyn.FFF)),
            (v.fff_setting, partial(m.on_dynamics_changed, Dyn.FFF)),
            (v.ffff_slider, partial(m.on_dynamics_changed, Dyn.FFFF)),
            (v.ffff_setting, partial(m.on_dynamics_changed, Dyn.FFFF)),
            (v.interpolate, m.on_interpolate_changed),
            # Instrument articulation settings
            (v.artic_default_length_slider, partial(alen, Artic.DEFAULT)),
            (v.artic_default_length_setting, partial(alen, Artic.DEFAULT)),
            (v.artic_default_volume_slider, partial(avol, Artic.DEFAULT)),
            (v.artic_default_volume_setting, partial(avol, Artic.DEFAULT)),
            (v.artic_acc_length_slider, partial(alen, Artic.ACCENT)),
            (v.artic_acc_length_setting, partial(alen, Artic.ACCENT)),
            (v.artic_acc_volume_slider, partial(avol, Artic.ACCENT)),
            (v.artic_acc_volume_setting, partial(avol, Artic.ACCENT)),
            (v.artic_stacc_length_slider, partial(alen, Artic.STACCATO)),
            (v.artic_stacc_length_setting, partial(alen, Artic.STACCATO)),
            (v.artic_stacc_volume_slider, partial(avol, Artic.STACCATO)),
            (v.artic_stacc_volume_setting, partial(avol, Artic.STACCATO)),
            (v.artic_accstacc_length_slider, partial(alen, Artic.ACCSTAC)),
            (v.artic_accstacc_length_setting, partial(alen, Artic.ACCSTAC)),
            (v.artic_accstacc_volume_slider, partial(avol, Artic.ACCSTAC)),
            (v.artic_accstacc_volume_setting, partial(avol, Artic.ACCSTAC)),
            # Instrument pan settings
            (v.pan_enable, m.on_pan_enable_changed),
            (v.pan_setting, m.on_pan_setting_changed),
            # Instrument sample
            (v.select_builtin_sample, m.on_builtin_sample_selected),
            (v.builtin_sample, m.on_builtin_sample_changed),
            (v.select_pack_sample, m.on_pack_sample_selected),
            (v.sample_pack_list, m.on_pack_sample_changed),
            (v.select_brr_sample, m.on_brr_sample_selected),
            (v.select_brr_fname, self.on_brr_clicked),
            (v.brr_fname, m.on_brr_fname_changed),
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
            (v.echo_enable, partial(m.on_echo_en_changed, EchoCh.GLOBAL)),
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

        for widget, slot in connections:
            if isinstance(widget, QPushButton):
                widget.clicked.connect(slot)
            elif isinstance(widget, QCheckBox):
                widget.stateChanged.connect(slot)
            elif isinstance(widget, QLineEdit):

                def proxy(widget=widget, slot=slot):
                    slot(widget.text())

                widget.editingFinished.connect(proxy)
            elif isinstance(widget, QRadioButton):
                widget.toggled.connect(slot)
            elif isinstance(widget, QAbstractSlider):
                widget.valueChanged.connect(slot)
            elif isinstance(widget, QAbstractItemView):
                widget.selectionModel().currentChanged.connect(slot)

        # Return signals
        m.state_changed.connect(self.on_state_changed)
        m.instruments_changed.connect(self.on_instruments_changed)

    ###########################################################################

    def _create_project(self) -> None:
        fname, _ = QFileDialog.getSaveFileName(
            self._view, "Project File", filter=f"*.{self._extension}"
        )
        if fname:
            self._model.create_project(pathlib.Path(fname))

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

    def _generate_mml(self, fname: str, echo: EchoConfig | None) -> None:
        if self._quicklook.isVisible() or fname:
            self._model.generate_mml(fname, echo)
        else:
            self._view.log_response(
                True,
                "Generation Error",
                "Select an MML file or open the Quicklook",
            )

    ###########################################################################

    def _open_project(self) -> None:
        fname, _ = QFileDialog.getOpenFileName(
            self._view, "Project File", filter=f"*.{self._extension}"
        )
        if fname:
            self._model.load(fname)

    ###########################################################################

    def _open_preferences(self) -> None:
        self._preferences.exec()

    ###########################################################################

    def _setup_menus(self) -> None:
        view = self._view
        model = self._model

        view.new_project.triggered.connect(self._create_project)
        view.open_project.triggered.connect(self._open_project)
        view.save_project.triggered.connect(model.save)
        view.close_project.triggered.connect(lambda _: None)
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

        if adsr_mode:
            env.plot_adsr(attack_reg, decay_reg, sus_level_reg, sus_rate_reg)
        else:  # gain mode
            match gain_mode:
                case GainMode.DIRECT:
                    env.plot_direct_gain(gain_reg)
                case GainMode.INCLIN:
                    env.plot_inclin(gain_reg)
                case GainMode.INCBENT:
                    env.plot_incbent(gain_reg)
                case GainMode.DECLIN:
                    env.plot_declin(gain_reg)
                case GainMode.DECEXP:
                    env.plot_decexp(gain_reg)

    ###########################################################################

    def _update_gain_limits(self, direct_mode: bool) -> None:
        view = self._view
        if direct_mode:
            view.gain_slider.setMaximum(127)
        else:
            val = min(31, view.gain_slider.value())
            view.gain_slider.setValue(val)
            view.gain_slider.setMaximum(31)
