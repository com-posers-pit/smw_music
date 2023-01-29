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
from typing import Callable

# Library imports
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QDoubleValidator, QIntValidator, QValidator
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QLabel,
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
from smw_music.ui import sample
from smw_music.ui.envelope_preview import EnvelopePreview
from smw_music.ui.model import Model
from smw_music.ui.preferences import Preferences
from smw_music.utils import hexb

###############################################################################
# Private function definitions
###############################################################################


def _btn_con(button: QPushButton, slot) -> None:
    button.clicked.connect(slot)


def _box_con(checkbox: QCheckBox, slot) -> None:
    checkbox.stateChanged.connect(slot)


def _edt_con(edit: QLineEdit, slot) -> None:
    edit.textEdited.connect(slot)


def _rad_con(radio: QRadioButton, slot) -> None:
    radio.toggled.connect(slot)


def _sld_con(slider: QSlider, slot) -> None:
    slider.valueChanged.connect(slot)


def _hookup_slider(
    slider: QSlider,
    edit: QLineEdit,
    label: QLabel,
    slider_to_edit: Callable[[int], str],
    edit_to_slider: Callable[[str], int],
    slider_to_label: Callable[[int], str],
    init: str,
    validator: QValidator | None,
) -> None:

    if validator:
        edit.setValidator(validator)

    slider.valueChanged.connect(lambda x: edit.setText(slider_to_edit(x)))
    slider.valueChanged.connect(lambda x: label.setText(slider_to_label(x)))
    edit.editingFinished.connect(
        lambda: slider.setValue(edit_to_slider(edit.text()))
    )

    edit.insert(init)
    edit.editingFinished.emit()


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
        #        self._preferences = Preferences()
        self._model = Model()

        self._edit = QTextEdit()
        self._quicklook = QMainWindow(parent=self._view)
        self._quicklook.setMinimumSize(800, 600)
        self._quicklook.setCentralWidget(self._edit)

        self._envelope_preview = EnvelopePreview(self._view)

        self._view.sample_pack_list.setModel(self._model.sample_packs_model)
        self._view.instrument_list.setModel(self._model.instruments_model)

        self._setup_menus()
        self._attach_signals()

        self._view.show()

    ###########################################################################
    # API method definitions
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

    def on_musicxml_fname_clicked(self) -> None:
        pass

    def on_mml_fname_clicked(self) -> None:
        pass

    def on_open_quicklook_clicked(self) -> None:
        self._quicklook.show()

    def on_brr_clicked(self) -> None:
        pass

    def on_preview_envelope_clicked(self) -> None:
        self._envelope_preview.show()

    ###########################################################################

    def _attach_signals(self) -> None:  # pylint: disable=too-many-statements
        m = self._model  # pylint: disable=invalid-name
        v = self._view  # pylint: disable=invalid-name

        # Control Panel
        _btn_con(v.select_musicxml_fname, self.on_musicxml_fname_clicked)
        _edt_con(v.musicxml_fname, m.on_musicxml_changed)
        _btn_con(v.select_mml_fname, self.on_mml_fname_clicked)
        _edt_con(v.mml_fname, m.on_mml_fname_changed)
        _box_con(v.loop_analysis, m.on_loop_analysis_changed)
        _box_con(v.superloop_analysis, m.on_superloop_analysis_changed)
        _box_con(v.measure_numbers, m.on_measure_numbers_changed)
        _btn_con(v.open_quicklook, self.on_open_quicklook_clicked)
        _btn_con(v.generate_mml, m.on_generate_mml_clicked)
        _btn_con(v.generate_spc, m.on_generate_spc_clicked)
        _btn_con(v.play_spc, m.on_play_spc_clicked)

        # Instrument dynamics settings
        _sld_con(v.pppp_slider, m.on_pppp_changed)
        _edt_con(v.pppp_setting, m.on_pppp_changed)
        _sld_con(v.ppp_slider, m.on_ppp_changed)
        _edt_con(v.ppp_setting, m.on_ppp_changed)
        _sld_con(v.pp_slider, m.on_pp_changed)
        _edt_con(v.pp_setting, m.on_pp_changed)
        _sld_con(v.p_slider, m.on_p_changed)
        _edt_con(v.p_setting, m.on_p_changed)
        _sld_con(v.mp_slider, m.on_mp_changed)
        _edt_con(v.mp_setting, m.on_mp_changed)
        _sld_con(v.mf_slider, m.on_mf_changed)
        _edt_con(v.mf_setting, m.on_mf_changed)
        _sld_con(v.f_slider, m.on_f_changed)
        _edt_con(v.f_setting, m.on_f_changed)
        _sld_con(v.ff_slider, m.on_ff_changed)
        _edt_con(v.ff_setting, m.on_ff_changed)
        _sld_con(v.fff_slider, m.on_fff_changed)
        _edt_con(v.fff_setting, m.on_fff_changed)
        _sld_con(v.ffff_slider, m.on_ffff_changed)
        _edt_con(v.ffff_setting, m.on_ffff_changed)
        _box_con(v.interpolate, m.on_interpolate_changed)

        # Instrument articulation settings
        _sld_con(v.artic_default_length_slider, m.on_def_artic_length_changed)
        _sld_con(v.artic_default_volume_slider, m.on_def_artic_volume_changed)
        _sld_con(v.artic_acc_length_slider, m.on_accent_length_changed)
        _sld_con(v.artic_acc_volume_slider, m.on_accent_volume_changed)
        _sld_con(v.artic_stacc_length_slider, m.on_staccato_length_changed)
        _sld_con(v.artic_stacc_volume_slider, m.on_staccato_volume_changed)
        _sld_con(v.artic_accstacc_length_slider, m.on_accstacc_length_changed)
        _sld_con(v.artic_accstacc_volume_slider, m.on_accstacc_volume_changed)

        # Instrument pan settings
        _btn_con(v.pan_enable, m.on_pan_enable_changed)
        _sld_con(v.pan_setting, m.on_pan_setting_changed)

        # Instrument sample
        _rad_con(v.select_builtin_sample, m.on_builtin_sample_selected)
        _rad_con(v.select_pack_sample, m.on_pack_sample_selected)
        _rad_con(v.select_brr_sample, m.on_brr_sample_selected)
        _btn_con(v.select_brr_fname, self.on_brr_clicked)
        _edt_con(v.brr_fname, m.on_brr_fname_changed)

        _rad_con(v.select_adsr_mode, m.on_select_adsr_mode_selected)
        _rad_con(v.gain_mode_direct, m.on_gain_direct_selected)
        _rad_con(v.gain_mode_inclin, m.on_gain_inclin_selected)
        _rad_con(v.gain_mode_incbent, m.on_gain_incbent_selected)
        _rad_con(v.gain_mode_declin, m.on_gain_declin_selected)
        _rad_con(v.gain_mode_decexp, m.on_gain_decexp_selected)
        _sld_con(v.gain_slider, m.on_gain_changed)
        _sld_con(v.attack_slider, m.on_attack_changed)
        _sld_con(v.decay_slider, m.on_decay_changed)
        _sld_con(v.sus_level_slider, m.on_sus_level_changed)
        _sld_con(v.sus_rate_slider, m.on_sus_rate_changed)

        _sld_con(v.tune_slider, m.on_tune_changed)
        _edt_con(v.tune_setting, m.on_tune_changed)
        _sld_con(v.subtune_slider, m.on_subtune_changed)
        _edt_con(v.subtune_setting, m.on_subtune_changed)

        _edt_con(v.brr_setting, m.on_brr_setting_changed)
        _btn_con(v.preview_envelope, self.on_preview_envelope_clicked)

        # Global settings
        _sld_con(v.global_volume_slider, m.on_global_volume_changed)
        _edt_con(v.global_volume_setting, m.on_global_volume_changed)
        _box_con(v.global_legato, m.on_global_legato_changed)
        _box_con(v.echo_enable, m.on_echo_enable_changed)
        _box_con(v.echo_ch0, m.on_echo_ch0_changed)
        _box_con(v.echo_ch1, m.on_echo_ch1_changed)
        _box_con(v.echo_ch2, m.on_echo_ch2_changed)
        _box_con(v.echo_ch3, m.on_echo_ch3_changed)
        _box_con(v.echo_ch4, m.on_echo_ch4_changed)
        _box_con(v.echo_ch5, m.on_echo_ch5_changed)
        _box_con(v.echo_ch6, m.on_echo_ch6_changed)
        _box_con(v.echo_ch7, m.on_echo_ch7_changed)
        _rad_con(v.echo_filter_0, m.on_filter_0_toggled)
        _sld_con(v.echo_left_slider, m.on_echo_left_changed)
        _edt_con(v.echo_left_setting, m.on_echo_left_changed)
        _box_con(v.echo_left_surround, m.on_echo_left_surround_changed)
        _sld_con(v.echo_right_slider, m.on_echo_right_changed)
        _edt_con(v.echo_right_setting, m.on_echo_right_changed)
        _box_con(v.echo_right_surround, m.on_echo_right_surround_changed)
        _sld_con(v.echo_feedback_slider, m.on_echo_feedback_changed)
        _edt_con(v.echo_feedback_setting, m.on_echo_feedback_changed)
        _box_con(v.echo_feedback_surround, m.on_echo_feedback_surround_changed)
        _sld_con(v.echo_delay_slider, m.on_echo_delay_changed)
        _edt_con(v.echo_delay_setting, m.on_echo_delay_changed)

    ###########################################################################

    def _update_gain_limits(self, toggled: bool) -> None:
        view = self._view
        if toggled:
            view.gain_slider.setMaximum(127)
        else:
            val = min(31, view.gain_slider.value())
            view.gain_slider.setValue(val)
            view.gain_slider.setMaximum(31)

    ###########################################################################

    def _update_setting(self) -> None:
        view = self._view

        adsr_mode = view.select_adsr_mode.isChecked()

        attack_reg = view.attack_slider.value()
        decay_reg = view.decay_slider.value()
        sus_level_reg = view.sus_level_slider.value()
        sus_rate_reg = view.sus_rate_slider.value()
        gain_reg = view.gain_slider.value()

        vxadsr1 = (int(adsr_mode) << 7) | (decay_reg << 4) | attack_reg
        vxadsr2 = (sus_level_reg << 5) | sus_rate_reg

        if view.gain_mode_direct.isChecked():
            vxgain = gain_reg
        elif view.gain_mode_inclin.isChecked():
            vxgain = 0xC0 | gain_reg
        elif view.gain_mode_incbent.isChecked():
            vxgain = 0xE0 | gain_reg
        elif view.gain_mode_declin.isChecked():
            vxgain = 0x80 | gain_reg
        elif view.gain_mode_decexp.isChecked():
            vxgain = 0xA0 | gain_reg

        # The register values for the mode we're not in are don't care; exo
        # likes the convention of setting them to 0.  Who am I to argue?
        if adsr_mode:
            vxgain = 0
        else:
            vxadsr1 = 0
            vxadsr2 = 0

        tune = view.tune_slider.value()
        subtune = view.subtune_slider.value()
        regs = [vxadsr1, vxadsr2, vxgain, tune, subtune]
        view.brr_setting.setText(" ".join(hexb(x) for x in regs))

    ###########################################################################

    def _update_envelope(self) -> None:
        view = self._view
        env = self._envelope_preview

        gain_reg = view.gain_slider.value()

        if view.select_adsr_mode.isChecked():
            env.plot_adsr(
                view.attack_slider.value(),
                view.decay_slider.value(),
                view.sus_level_slider.value(),
                view.sus_rate_slider.value(),
            )
        else:  # view.select_gain_mode
            if view.gain_mode_direct.isChecked():
                env.plot_direct_gain(gain_reg)
            elif view.gain_mode_inclin.isChecked():
                env.plot_inclin(gain_reg)
            elif view.gain_mode_incbent.isChecked():
                env.plot_incbent(gain_reg)
            elif view.gain_mode_declin.isChecked():
                env.plot_declin(gain_reg)
            elif view.gain_mode_decexp.isChecked():
                env.plot_decexp(gain_reg)

        self._update_setting()

    ###########################################################################

    def _create_project(self) -> None:
        fname, _ = QFileDialog.getSaveFileName(
            self._view, "Project File", filter=f"*.{self._extension}"
        )
        if fname:
            self._model.create_project(pathlib.Path(fname))

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

        view.new_project.triggered.connect(self._create_project)
        view.open_project.triggered.connect(self._open_project)
        view.save_project.triggered.connect(self._model.save)
        view.close_project.triggered.connect(lambda _: None)
        view.open_preferences.triggered.connect(self._open_preferences)
        view.exit_dashboard.triggered.connect(QApplication.quit)

        view.undo.triggered.connect(lambda _: None)
        view.redo.triggered.connect(lambda _: None)

        view.show_about.triggered.connect(self._about)
        view.show_about_qt.triggered.connect(QApplication.aboutQt)
