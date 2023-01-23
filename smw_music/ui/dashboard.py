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
from smw_music.ui.controller import Controller
from smw_music.ui.model import Model

###############################################################################
# Private function definitions
###############################################################################


def _make_file_picker(
    button: QPushButton, edit: QLineEdit, save: bool, caption: str, filt: str
) -> None:
    def callback():
        if save:
            dlg = QFileDialog.getSaveFileName
        else:
            dlg = QFileDialog.getOpenFileName
        fname, _ = dlg(button, caption=caption, filter=filt)
        if fname:
            edit.setText(fname)

    button.clicked.connect(callback)


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
    _extension = "prj"
    _model: Model
    _view: QMainWindow

    ###########################################################################
    # Constructor definitions
    ###########################################################################

    def __init__(self):
        ui_contents = pkgutil.get_data("smw_music", "/data/dashboard.ui")
        if ui_contents is None:
            raise Exception("Can't locate dashboard")

        self._model = Model()
        self._view = uic.loadUi(io.BytesIO(ui_contents))

        self._edit = QTextEdit()
        self._edit_window = QMainWindow(parent=self._view)
        self._edit_window.setMinimumSize(800, 600)
        self._edit_window.setCentralWidget(self._edit)

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
        text += "\nCopyright Ⓒ 2022 The SMW Music Python Project Authors"
        text += "\nHomepage: https://github.com/com-posers-pit/smw_music"

        QMessageBox.about(self._view, title, text)

    ###########################################################################

    def _attach_signals(self) -> None:
        model = self._model
        view = self._view

        view.musicxml_fname.textChanged.connect(model.set_song)
        view.play_spc.clicked.connect(model.play_spc)
        view.generate_mml.clicked.connect(self._generate_mml)
        view.open_quicklook.clicked.connect(self._edit_window.show)
        model.song_changed.connect(self.update_song)
        # controller.mml_converted.connect(model.convert_mml)

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

    def _create_project(self) -> None:
        fname, _ = QFileDialog.getSaveFileName(
            self._view, "Project File", filter=f"*.{self._extension}"
        )
        if fname:
            self._model.create_project(pathlib.Path(fname))

    ###########################################################################

    def _finish_ui_setup(self) -> None:
        view = self._view
        _make_file_picker(
            view.select_musicxml_fname,
            view.musicxml_fname,
            False,
            "Input MusicXML File",
            "MusicXML (*.mxl *.musicxml);;Any (*)",
        )
        _make_file_picker(
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

    def _preferences(self) -> None:
        pass

    ###########################################################################

    def _setup_menus(self) -> None:
        view = self._view

        view.new_project.triggered.connect(self._create_project)
        view.open_project.triggered.connect(self._open_project)
        view.save_project.triggered.connect(self._model.save)
        view.close_project.triggered.connect(lambda _: None)
        view.open_preferences.triggered.connect(self._preferences)
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
