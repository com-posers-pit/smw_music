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
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QTextEdit,
)

# Package imports
from smw_music import __version__
from smw_music.music_xml.echo import EchoConfig
from smw_music.music_xml.song import Song
from smw_music.ui import sample
from smw_music.ui.controller import Controller
from smw_music.ui.envelope_preview import EnvelopePreview
from smw_music.ui.file_picker import file_picker
from smw_music.ui.model import Model
from smw_music.ui.preferences import Preferences

###############################################################################
# Private function definitions
###############################################################################


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
    _edit_window: QMainWindow
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
        self._edit_window = QMainWindow(parent=self._view)
        self._edit_window.setMinimumSize(800, 600)
        self._edit_window.setCentralWidget(self._edit)

        self._envelope_preview = EnvelopePreview(self._view)

        self._view.sample_pack_list.setModel(self._model.sample_packs_model)
        self._view.instrument_list.setModel(self._model.instruments_model)

        self._finish_ui_setup()
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

    def _attach_signals(self) -> None:
        model = self._model
        view = self._view

        view.generate_mml.clicked.connect(
            model.on_mml_generated
        )  # TODO: port this over self._generate_mml
        view.generate_spc.clicked.connect(model.on_spc_generated)
        view.play_spc.clicked.connect(model.on_spc_played)

        view.preview_envelope.clicked.connect(self._envelope_preview.show)

        view.select_adsr_mode.released.connect(self._update_envelope)
        view.select_gain_mode.released.connect(self._update_envelope)
        view.gain_mode_direct.released.connect(self._update_envelope)
        view.gain_mode_inclin.released.connect(self._update_envelope)
        view.gain_mode_incbent.released.connect(self._update_envelope)
        view.gain_mode_declin.released.connect(self._update_envelope)
        view.gain_mode_decexp.released.connect(self._update_envelope)
        view.gain_slider.valueChanged.connect(self._update_envelope)
        view.attack_slider.valueChanged.connect(self._update_envelope)
        view.decay_slider.valueChanged.connect(self._update_envelope)
        view.sus_level_slider.valueChanged.connect(self._update_envelope)
        view.sus_rate_slider.valueChanged.connect(self._update_envelope)

        view.gain_mode_direct.toggled.connect(self._update_gain_limits)
        view.gain_slider.valueChanged.connect(
            lambda x: view.gain_setting_label.setText(f"x{x:02x}")
        )

        view.attack_slider.valueChanged.connect(
            lambda x: view.attack_setting_label.setText(f"x{x:02x}")
        )
        view.attack_slider.valueChanged.connect(
            lambda x: view.attack_eu_label.setText(sample.attack_dn2eu(x))
        )
        view.decay_slider.valueChanged.connect(
            lambda x: view.decay_setting_label.setText(f"x{x:02x}")
        )
        view.decay_slider.valueChanged.connect(
            lambda x: view.decay_eu_label.setText(sample.decay_dn2eu(x))
        )
        view.sus_level_slider.valueChanged.connect(
            lambda x: view.sus_level_setting_label.setText(f"x{x:02x}")
        )
        view.sus_level_slider.valueChanged.connect(
            lambda x: view.sus_level_eu_label.setText(
                sample.sus_level_dn2eu(x)
            )
        )
        view.sus_rate_slider.valueChanged.connect(
            lambda x: view.sus_rate_setting_label.setText(f"x{x:02x}")
        )
        view.sus_rate_slider.valueChanged.connect(
            lambda x: view.sus_rate_eu_label.setText(sample.sus_rate_dn2eu(x))
        )

        view.tune_slider.valueChanged.connect(self._update_setting)
        view.tune_slider.valueChanged.connect(
            lambda x: view.tune_setting.setText(f"x{x:02x}")
        )
        view.subtune_slider.valueChanged.connect(self._update_setting)
        view.subtune_slider.valueChanged.connect(
            lambda x: view.subtune_setting.setText(f"x{x:02x}")
        )

    #        view.musicxml_fname.textChanged.connect(model.set_song)
    #        view.open_quicklook.clicked.connect(self._edit_window.show)
    #        model.song_changed.connect(self.update_song)

    # controller.artic_changed.connect(model.update_artic)
    # controller.config_changed.connect(model.set_config)
    # controller.instrument_changed.connect(model.set_instrument)
    # controller.pan_changed.connect(model.set_pan)
    # controller.song_changed.connect(model.set_song)
    # controller.volume_changed.connect(model.update_dynamics)
    # model.inst_config_changed.connect(controller.change_inst_config)
    # model.mml_generated.connect(self._edit.setText)
    # model.response_generated.connect(controller.log_response)
    # model.song_changed.connect(controller.update_song)

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
        view.brr_setting.setText(
            f"x{vxadsr1:02x} x{vxadsr2:02x} x{vxgain:02x} x{tune:02x} x{subtune:02x}"
        )

    ###########################################################################
    def _update_envelope(self) -> None:
        view = self._view
        env = self._envelope_preview

        gain_reg = view.gain_slider.value()

        if view.select_adsr_mode.isChecked():
            env.adsr(
                view.attack_slider.value(),
                view.decay_slider.value(),
                view.sus_level_slider.value(),
                view.sus_rate_slider.value(),
            )
        else:  # view.select_gain_mode
            if view.gain_mode_direct.isChecked():
                env.direct_gain(gain_reg)
            elif view.gain_mode_inclin.isChecked():
                env.inclin(gain_reg)
            elif view.gain_mode_incbent.isChecked():
                env.incbent(gain_reg)
            elif view.gain_mode_declin.isChecked():
                env.declin(gain_reg)
            elif view.gain_mode_decexp.isChecked():
                env.decexp(gain_reg)

        self._update_setting()

    ###########################################################################

    def _create_project(self) -> None:
        fname, _ = QFileDialog.getSaveFileName(
            self._view, "Project File", filter=f"*.{self._extension}"
        )
        if fname:
            self._model.create_project(pathlib.Path(fname))

    ###########################################################################

    def _finish_ui_setup(self) -> None:
        view = self._view
        file_picker(
            view.select_musicxml_fname,
            view.musicxml_fname,
            False,
            "Input MusicXML File",
            "MusicXML (*.mxl *.musicxml);;Any (*)",
        )
        file_picker(
            view.select_mml_fname,
            view.mml_fname,
            True,
            "Output MusicXML File",
            "",
        )

        # self._hookup_sample_sliders()
        self._hookup_vol_sliders()

    ###########################################################################

    def _generate_mml(self, fname: str, echo: EchoConfig | None) -> None:
        if self._edit_window.isVisible() or fname:
            self._model.generate_mml(fname, echo)
        else:
            self._view.log_response(
                True,
                "Generation Error",
                "Select an MML file or open the Quicklook",
            )

    ###########################################################################

    def _hookup_sample_sliders(self) -> None:
        view = self._view
        dyn = [
            (
                view.attack_slider,
                view.attack_setting,
                view.attack_setting_label,
            ),
            (view.decay_slider, view.decay_setting, view.decay_setting_label),
            (
                view.sustain_slider,
                view.sustain_setting,
                view.sustain_setting_label,
            ),
            (
                view.release_slider,
                view.release_setting,
                view.release_setting_label,
            ),
            (view.gain_slider, view.gain_setting, view.gain_setting_label),
            (view.tune_slider, view.tune_setting, view.tune_setting_label),
            (
                view.subtune_slider,
                view.subtune_setting,
                view.subtune_setting_label,
            ),
        ]

        for slider, setting, label in dyn:
            _hookup_slider(
                slider,
                setting,
                label,
                lambda x: "",
                lambda x: 0,
                lambda x: "",
                "0",
                None,
            )

    ###########################################################################

    def _hookup_vol_sliders(self) -> None:
        view = self._view
        dyn = [
            (view.pppp_slider, view.pppp_setting, view.pppp_setting_label),
            (view.ppp_slider, view.ppp_setting, view.ppp_setting_label),
            (view.pp_slider, view.pp_setting, view.pp_setting_label),
            (view.p_slider, view.p_setting, view.p_setting_label),
            (view.mp_slider, view.mp_setting, view.mp_setting_label),
            (view.mf_slider, view.mf_setting, view.mf_setting_label),
            (view.f_slider, view.f_setting, view.f_setting_label),
            (view.ff_slider, view.ff_setting, view.ff_setting_label),
            (view.fff_slider, view.fff_setting, view.fff_setting_label),
            (view.ffff_slider, view.ffff_setting, view.ffff_setting_label),
        ]

        for slider, setting, label in dyn:
            _hookup_slider(
                slider,
                setting,
                label,
                lambda x: f"{100*x/255:5.1f}",
                lambda x: int(255 * float(x) / 100),
                lambda x: f"x{x:02x}",
                "0",
                QDoubleValidator(0, 100, 1),
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


###############################################################################


class Dashboard2(QMainWindow):
    _extension = "prj"

    ###########################################################################

    def __init__(self) -> None:
        super().__init__()

        self._model = Model()
        self._controller = Controller()
        self._edit_window = QMainWindow(parent=self)
        self._edit = QTextEdit()
        self._controller.load_sample_packs(self._model.sample_packs_model)

        self._edit_window.setMinimumSize(800, 600)

        self._setup_menus()
        self._setup_output()
        self._attach_signals()

        self.setCentralWidget(self._controller)

    ###########################################################################
    # Private method definitions
    ###########################################################################

    def _about(self) -> None:
        title = "About MusicXML -> MML"
        text = f"Version: {__version__}"
        text += "\nCopyright Ⓒ 2022 The SMW Music Python Project Authors"
        text += "\nHomepage: https://github.com/com-posers-pit/smw_music"

        QMessageBox.about(self, title, text)

    ###########################################################################

    def _attach_signals(self) -> None:
        controller = self._controller
        model = self._model

        controller.artic_changed.connect(model.update_artic)
        controller.config_changed.connect(model.set_config)
        controller.instrument_changed.connect(model.set_instrument)
        controller.mml_requested.connect(self._generate_mml)
        controller.mml_converted.connect(model.convert_mml)
        controller.pan_changed.connect(model.set_pan)
        controller.quicklook_opened.connect(self._edit_window.show)
        controller.song_changed.connect(model.set_song)
        controller.spc_played.connect(model.play_spc)
        controller.volume_changed.connect(model.update_dynamics)
        model.inst_config_changed.connect(controller.change_inst_config)
        model.mml_generated.connect(self._edit.setText)
        model.response_generated.connect(controller.log_response)
        model.song_changed.connect(controller.update_song)

    ###########################################################################

    def _create_project(self) -> None:
        fname, _ = QFileDialog.getSaveFileName(
            self, "Project File", filter=f"*.{self._extension}"
        )
        if fname:
            self._model.create_project(pathlib.Path(fname))

    ###########################################################################

    def _generate_mml(self, fname: str, echo: EchoConfig | None) -> None:
        if self._edit_window.isVisible() or fname:
            self._model.generate_mml(fname, echo)
        else:
            self._controller.log_response(
                True,
                "Generation Error",
                "Select an MML file or open the Quicklook",
            )

    ###########################################################################

    def _open_project(self) -> None:
        fname, _ = QFileDialog.getOpenFileName(
            self, "Project File", filter=f"*.{self._extension}"
        )
        if fname:
            self._model.load(fname)

    ###########################################################################

    def _preferences(self) -> None:
        pass

    ###########################################################################

    def _save_as(self) -> None:
        fname, _ = QFileDialog.getSaveFileName(
            self, "Project File", filter=f"*.{self._extension}"
        )
        if fname:
            self._model.save_as(fname)

    ###########################################################################

    def _setup_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("&New Project...", self._create_project)
        file_menu.addAction("&Open Project...", self._open_project)
        file_menu.addAction("&Save", self._model.save)
        file_menu.addAction("&Close Project...", lambda _: None)
        file_menu.addSeparator()
        file_menu.addAction("&Preferences", self._preferences)
        file_menu.addSeparator()
        file_menu.addAction("&Quit", QApplication.quit)

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction("About", self._about)
        help_menu.addAction("About Qt", QApplication.aboutQt)

    ###########################################################################

    def _setup_output(self) -> None:
        self._edit.setReadOnly(True)
        self._edit.setFontFamily("Courier")
        self._edit_window.setCentralWidget(self._edit)
